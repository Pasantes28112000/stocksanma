# dashboard_caja.py
import customtkinter as ctk
import tkinter.messagebox as mb
from lib_db import get_connection

class CajaFrame(ctk.CTkFrame):
    def __init__(self, parent, db_path):
        super().__init__(parent)
        self.db = db_path
        self.total_var = ctk.StringVar(value="0.00")
        self.build()
        self.update_contents()

    def build(self):
        header = ctk.CTkLabel(self, text="Caja", font=ctk.CTkFont(size=18, weight="bold"))
        header.pack(pady=6)
        frame = ctk.CTkFrame(self)
        frame.pack(padx=12, pady=12, fill="x")
        ctk.CTkLabel(frame, text="Total en caja").grid(row=0, column=0, sticky="w", pady=6)
        self.total_entry = ctk.CTkEntry(frame, textvariable=self.total_var, width=180)
        self.total_entry.grid(row=0, column=1, pady=6, padx=6)
        ctk.CTkButton(frame, text="Actualizar", command=self.update_contents).grid(row=1, column=0, pady=6)
        ctk.CTkButton(frame, text="Modificar", command=self._modificar).grid(row=1, column=1, pady=6)
        ctk.CTkButton(frame, text="+ Agregar", command=lambda: self._cambiar_signo(+1)).grid(row=2, column=0, pady=6)
        ctk.CTkButton(frame, text="- Quitar", command=lambda: self._cambiar_signo(-1)).grid(row=2, column=1, pady=6)

    def update_contents(self):
        conn = get_connection(self.db)
        cur = conn.cursor()
        cur.execute("SELECT total FROM dinero WHERE id=1")
        row = cur.fetchone()
        conn.close()
        if row:
            self.total_var.set(f"{row[0]:.2f}")
        else:
            self.total_var.set("0.00")

    def _modificar(self):
        try:
            nuevo = float(self.total_var.get())
            conn = get_connection(self.db)
            cur = conn.cursor()
            cur.execute("UPDATE dinero SET total=? WHERE id=1", (nuevo,))
            conn.commit()
            conn.close()
            mb.showinfo("Caja", "Total actualizado")
        except Exception as e:
            mb.showerror("Error", str(e))

    def _cambiar_signo(self, signo):
        import tkinter.simpledialog as sd
        try:
            monto = sd.askfloat("Monto", "Ingrese monto:")
            if monto is None:
                return
            conn = get_connection(self.db)
            cur = conn.cursor()
            cur.execute("UPDATE dinero SET total = total + ? WHERE id=1", (signo*monto,))
            conn.commit()
            conn.close()
            self.update_contents()
        except Exception as e:
            mb.showerror("Error", str(e))
