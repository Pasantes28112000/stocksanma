# funcs/dashboard_alertas.py
import customtkinter as ctk
import tkinter as tk
import sqlite3
from lib_db import load_config

class AlertasManager(ctk.CTkFrame):
    def __init__(self, parent, db_path):
        super().__init__(parent, width=120)
        self.db = db_path
        self.btn = ctk.CTkButton(self, text="🔔", width=80, command=self._open_alerts_window)
        self.btn.pack()
        self.alerts = []
        self.acknowledged = False
        try:
            self.check_alerts()
        except Exception:
            pass

    def check_alerts(self):
        conn = sqlite3.connect(self.db)
        cur = conn.cursor()
        cur.execute("SELECT cdb, nombre, cantidad, umbral FROM producto WHERE cantidad <= umbral")
        bajos = cur.fetchall()
        cur.execute("SELECT v.cdb, p.nombre, v.cantidad, v.fecha_vencimiento FROM vencimientos v LEFT JOIN producto p ON v.cdb=p.cdb WHERE v.fecha_vencimiento IS NOT NULL AND date(v.fecha_vencimiento) <= date('now', '+7 days')")
        prox = cur.fetchall()
        conn.close()
        self.alerts = []
        for b in bajos:
            self.alerts.append({"type":"stock", "msg": f"Stock bajo: {b[1]} (id {b[0]}) - {b[2]} <= umbral {b[3]}"})
        for p in prox:
            self.alerts.append({"type":"venc", "msg": f"Vencimiento: {p[1] or 'N/D'} (id {p[0]}) vence {p[3]}"})
        # if acknowledged, keep count 0 until next check (ack clears)
        cnt = 0 if self.acknowledged else len(self.alerts)
        self.btn.configure(text=f"🔔 {cnt}" if cnt else "🔔")
        return cnt

    def _open_alerts_window(self):
        # show alerts, and allow "marcar como leidas"
        self.check_alerts()
        win = tk.Toplevel(self)
        win.title("Alertas")
        win.geometry("420x320")
        win.transient(self.master)
        win.grab_set()
        frame = tk.Frame(win)
        frame.pack(fill="both", expand=True, padx=8, pady=8)
        if not self.alerts:
            tk.Label(frame, text="Sin alertas", font=("Arial", 12)).pack(pady=20)
            return
        lb = tk.Listbox(frame)
        lb.pack(fill="both", expand=True)
        for a in self.alerts:
            lb.insert(tk.END, a["msg"])
        btns = tk.Frame(win)
        btns.pack(fill="x", pady=6, padx=8)
        tk.Button(btns, text="Marcar como leídas", command=lambda: (self._acknowledge(win))).pack(side="left", padx=6)
        tk.Button(btns, text="Cerrar", command=win.destroy).pack(side="right", padx=6)

    def _acknowledge(self, win=None):
        # mark current alerts as read until next change
        self.acknowledged = True
        self.btn.configure(text="🔔")
        if win:
            win.destroy()

    def clear_alerts(self):
        # external button to clear current alerts
        self.acknowledged = True
        self.btn.configure(text="🔔")
