# ...existing code...
import customtkinter as ctk
import tkinter.messagebox as mb
from lib_db import get_connection
from utils import formatting
import re

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

    def _parse_amount_to_float(self, text):
        """
        Convierte un string formateado (posible símbolo, separadores) a float usando prefs actuales.
        """
        if text is None:
            return 0.0
        s = str(text).strip()

        prefs = getattr(formatting, "_prefs", {
            "currency_symbol": "$",
            "currency_position": "before",
            "decimal_separator": ".",
            "thousands_separator": ",",
            "decimal_places": 2
        })
        symbol = prefs.get("currency_symbol", "")
        dec = prefs.get("decimal_separator", ".")
        thou = prefs.get("thousands_separator", ",")

        # eliminar símbolo de moneda (tanto antes como después)
        if symbol:
            s = s.replace(symbol, "")

        # eliminar espacios y separador de miles
        s = s.replace(" ", "")
        if thou:
            s = s.replace(thou, "")

        # normalizar separador decimal a punto
        if dec and dec != ".":
            s = s.replace(dec, ".")

        # extraer la primera ocurrencia que parezca un número (incluye signo y punto)
        m = re.search(r"[-+]?\d+(?:\.\d+)?", s)
        if m:
            try:
                return float(m.group(0))
            except Exception:
                pass
        # fallback: intentar convertir directo
        try:
            return float(s)
        except Exception:
            raise ValueError(f"No se pudo interpretar monto: {text}")

    def update_contents(self):
        conn = get_connection(self.db)
        cur = conn.cursor()
        cur.execute("SELECT total FROM dinero WHERE id=1")
        row = cur.fetchone()
        conn.close()
        if row:
            try:
                # mostrar formateado con símbolo y separadores según prefs
                self.total_var.set(formatting.format_amount(row[0]))
            except Exception:
                # fallback a formato simple
                self.total_var.set(f"{row[0]:.2f}")
        else:
            try:
                self.total_var.set(formatting.format_amount(0.0))
            except Exception:
                self.total_var.set("0.00")

    def _modificar(self):
        try:
            texto = self.total_var.get()
            nuevo = self._parse_amount_to_float(texto)
            conn = get_connection(self.db)
            cur = conn.cursor()
            cur.execute("UPDATE dinero SET total=? WHERE id=1", (nuevo,))
            conn.commit()
            conn.close()
            mb.showinfo("Caja", "Total actualizado")
            self.update_contents()
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
# ...existing code...