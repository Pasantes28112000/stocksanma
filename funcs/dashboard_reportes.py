# dashboard_reportes.py
import customtkinter as ctk
import sqlite3
from lib_db import get_connection

class ReportesFrame(ctk.CTkFrame):
    def __init__(self, parent, db_path):
        super().__init__(parent)
        self.db = db_path
        self.build()

    def build(self):
        header = ctk.CTkLabel(self, text="Reportes", font=ctk.CTkFont(size=18, weight="bold"))
        header.pack(pady=6)
        ctk.CTkButton(self, text="Refrescar", command=self.update_contents).pack(pady=6)
        self.frame = ctk.CTkScrollableFrame(self)
        self.frame.pack(fill="both", expand=True, padx=12, pady=6)

    def update_contents(self):
        for w in self.frame.winfo_children():
            w.destroy()
        conn = get_connection(self.db)
        cur = conn.cursor()
        cur.execute("""SELECT v.id, v.fecha, vd.cdb, vd.cantidad, vd.precio_venta
                       FROM venta v JOIN venta_detalle vd ON v.id = vd.venta
                       ORDER BY v.fecha DESC LIMIT 200""")
        ventas = cur.fetchall()
        ctk.CTkLabel(self.frame, text="Ventas recientes").pack(anchor="w", padx=6, pady=4)
        for v in ventas:
            ctk.CTkLabel(self.frame, text=str(v)).pack(anchor="w", padx=6)

        cur.execute("""SELECT c.id, c.fecha, cd.cdb, cd.cantidad, cd.precio_compra
                       FROM compra c JOIN compra_detalle cd ON c.id = cd.compra
                       ORDER BY c.fecha DESC LIMIT 200""")
        compras = cur.fetchall()
        ctk.CTkLabel(self.frame, text="Compras recientes").pack(anchor="w", padx=6, pady=8)
        for c in compras:
            ctk.CTkLabel(self.frame, text=str(c)).pack(anchor="w", padx=6)
        conn.close()
