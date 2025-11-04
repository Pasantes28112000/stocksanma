# dashboard_alertas.py
import customtkinter as ctk
import tkinter.messagebox as mb
from lib_db import get_connection

class AlertasFrame(ctk.CTkFrame):
    def __init__(self, parent, db_path, notify_callback=None):
        super().__init__(parent)
        self.db = db_path
        self.notify_callback = notify_callback
        self.build()

    def build(self):
        header = ctk.CTkLabel(self, text="Alertas", font=ctk.CTkFont(size=18, weight="bold"))
        header.pack(pady=6)
        ctk.CTkButton(self, text="Refrescar", command=self.update_contents).pack(pady=6)
        self.frame = ctk.CTkScrollableFrame(self)
        self.frame.pack(fill="both", expand=True, padx=12, pady=6)

    def update_contents(self):
        for w in self.frame.winfo_children():
            w.destroy()
        conn = get_connection(self.db)
        cur = conn.cursor()
        # bajo stock
        cur.execute("SELECT cdb, nombre, cantidad, umbral FROM producto WHERE cantidad <= umbral")
        bajos = cur.fetchall()
        if bajos:
            ctk.CTkLabel(self.frame, text="Productos con bajo stock:").pack(anchor="w", padx=6, pady=4)
            for b in bajos:
                ctk.CTkLabel(self.frame, text=f"{b[0]} - {b[1]} (cant {b[2]} umbral {b[3]})").pack(anchor="w", padx=8)
        # proximos vencimientos 7 dias
        cur.execute("SELECT v.cdb, p.nombre, v.cantidad, v.fecha_vencimiento FROM vencimientos v JOIN producto p ON v.cdb=p.cdb WHERE v.fecha_vencimiento <= date('now', '+7 days')")
        prox = cur.fetchall()
        if prox:
            ctk.CTkLabel(self.frame, text="Próximos vencimientos (7 días):").pack(anchor="w", padx=6, pady=8)
            for p in prox:
                ctk.CTkLabel(self.frame, text=f"{p[0]} - {p[1]} (cant {p[2]}) vence {p[3]}").pack(anchor="w", padx=8)
        conn.close()
