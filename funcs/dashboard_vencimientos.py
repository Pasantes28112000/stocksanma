# dashboard_vencimientos.py
import customtkinter as ctk
import tkinter.messagebox as mb
from lib_db import get_connection, fetch_all_products
import datetime

class VencimientosFrame(ctk.CTkFrame):
    def __init__(self, parent, db_path):
        super().__init__(parent)
        self.db = db_path
        self.build()

    def build(self):
        header = ctk.CTkLabel(self, text="Vencimientos", font=ctk.CTkFont(size=18, weight="bold"))
        header.pack(pady=6)
        top = ctk.CTkFrame(self)
        top.pack(fill="x", padx=12, pady=6)
        ctk.CTkButton(top, text="Refrescar", command=self.update_contents).pack(side="left", padx=6)
        ctk.CTkButton(top, text="Añadir", command=self._add).pack(side="left", padx=6)
        ctk.CTkButton(top, text="Eliminar expirados", command=self._limpiar_expirados).pack(side="left", padx=6)
        self.list_frame = ctk.CTkScrollableFrame(self)
        self.list_frame.pack(fill="both", expand=True, padx=12, pady=6)

    def update_contents(self):
        for w in self.list_frame.winfo_children():
            w.destroy()
        conn = get_connection(self.db)
        cur = conn.cursor()
        cur.execute("SELECT cdb, cantidad, fecha_vencimiento FROM vencimientos ORDER BY fecha_vencimiento")
        rows = cur.fetchall()
        conn.close()
        for r in rows:
            cdb, cantidad, fv = r
            lbl = ctk.CTkLabel(self.list_frame, text=f"{cdb} - Cant: {cantidad} - Vto: {fv}")
            lbl.pack(fill="x", padx=6, pady=4)

    def _add(self):
        import tkinter.simpledialog as sd
        cdb = sd.askinteger("CDB", "Código de Barras:")
        if not cdb:
            return
        cantidad = sd.askinteger("Cantidad", "Cantidad:", minvalue=1)
        fecha = sd.askstring("Vencimiento", "Fecha (YYYY-MM-DD) o vacío")
        try:
            fecha_iso = None
            if fecha and fecha.strip():
                fecha_iso = datetime.date.fromisoformat(fecha.strip()).isoformat()
            conn = get_connection(self.db)
            cur = conn.cursor()
            cur.execute("INSERT INTO vencimientos (cdb, cantidad, fecha_vencimiento) VALUES (?, ?, ?)", (cdb, cantidad, fecha_iso))
            conn.commit()
            conn.close()
            self.update_contents()
        except Exception as e:
            mb.showerror("Error", str(e))

    def _limpiar_expirados(self):
        conn = get_connection(self.db)
        cur = conn.cursor()
        cur.execute("DELETE FROM vencimientos WHERE fecha_vencimiento < date('now')")
        conn.commit()
        conn.close()
        mb.showinfo("Limpieza", "Vencimientos expirados eliminados")
        self.update_contents()
