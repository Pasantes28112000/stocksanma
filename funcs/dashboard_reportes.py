# funcs/dashboard_reportes.py
import customtkinter as ctk
import sqlite3
from datetime import datetime

class ReportesFrame(ctk.CTkFrame):
    def __init__(self, parent, db_path):
        super().__init__(parent)
        self.db = db_path
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Reportes", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(8,12))
        top = ctk.CTkFrame(self)
        top.pack(fill="x", padx=12)
        ctk.CTkButton(top, text="Refrescar", command=self.update_contents).pack(side="left", padx=6)
        self.frame = ctk.CTkScrollableFrame(self)
        self.frame.pack(fill="both", expand=True, padx=12, pady=12)

    def update_contents(self):
        for w in self.frame.winfo_children():
            w.destroy()
        conn = sqlite3.connect(self.db)
        cur = conn.cursor()

        ctk.CTkLabel(self.frame, text="Ventas recientes").pack(anchor="w", padx=6, pady=(6,2))
        cur.execute("""SELECT v.id, v.fecha, SUM(vd.cantidad*vd.precio_venta) as total
                       FROM venta v JOIN venta_detalle vd ON v.id = vd.venta
                       GROUP BY v.id ORDER BY v.fecha DESC LIMIT 100""")
        ventas = cur.fetchall()
        for v in ventas:
            ctk.CTkLabel(self.frame, text=f"ID {v[0]} - {v[1]} - ${v[2]:.2f}").pack(anchor="w", padx=8)

        ctk.CTkLabel(self.frame, text="Compras recientes").pack(anchor="w", padx=6, pady=(12,2))
        cur.execute("""SELECT c.id, c.fecha, SUM(cd.cantidad*cd.precio_compra) as total
                       FROM compra c JOIN compra_detalle cd ON c.id = cd.compra
                       GROUP BY c.id ORDER BY c.fecha DESC LIMIT 100""")
        compras = cur.fetchall()
        for c in compras:
            ctk.CTkLabel(self.frame, text=f"ID {c[0]} - {c[1]} - ${c[2]:.2f}").pack(anchor="w", padx=8)

        # saldo caja
        cur.execute("SELECT total FROM dinero WHERE id=1")
        row = cur.fetchone()
        saldo = row[0] if row else 0.0
        ctk.CTkLabel(self.frame, text=f"Saldo caja: ${saldo:.2f}", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=6, pady=12)
        conn.close()
