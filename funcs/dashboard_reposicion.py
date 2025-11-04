# funcs/dashboard_reposicion.py
import customtkinter as ctk
import tkinter as tk
import sqlite3
from datetime import datetime
import tkinter.messagebox as mb
from lib_db import load_config

class ReposicionFrame(ctk.CTkFrame):
    def __init__(self, parent, db_path, config=None):
        super().__init__(parent)
        self.db = db_path
        self.config = config or load_config()
        self.reponer = []
        self._build_ui()
        self._load_products()

    def _build_ui(self):
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(header, text="Reposición de productos", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")
        self.search = ctk.CTkEntry(header, placeholder_text="Buscar por nombre o CDB")
        self.search.pack(side="left", padx=8)
        self.search.bind("<KeyRelease>", lambda e: self._load_products())
        ctk.CTkButton(header, text="Guardar cambios", command=self._guardar_reposicion).pack(side="right", padx=8)

        self.table = ctk.CTkScrollableFrame(self)
        self.table.pack(fill="both", expand=True, padx=10, pady=8)

    def update_contents(self):
        self._load_products()

    def _load_products(self):
        for w in self.table.winfo_children():
            w.destroy()
        q = self.search.get().strip().lower()
        conn = sqlite3.connect(self.db)
        cur = conn.cursor()
        cur.execute("SELECT cdb, nombre, cantidad, umbral FROM producto ORDER BY nombre")
        rows = cur.fetchall()
        conn.close()

        hdr = ctk.CTkLabel(self.table, text=f"{'CDB':<8}{'Nombre':<25}{'Stock':>8}{'Umbral':>8}")
        hdr.pack(anchor="w", padx=6, pady=(6,4))

        for r in rows:
            cdb, nombre, stock, umbral = r
            if q and q not in str(cdb).lower() and q not in (nombre or "").lower():
                continue
            row = ctk.CTkFrame(self.table)
            row.pack(fill="x", padx=6, pady=2)
            ctk.CTkLabel(row, text=f"{cdb:<8}{nombre[:25]:<25}{stock:>8}{umbral:>8}", anchor="w").pack(side="left", padx=4)
            ctk.CTkButton(row, text="Agregar", width=100, command=lambda p=r: self._select(p)).pack(side="right", padx=6)

    def _select(self, producto):
        cdb, nombre, stock, umbral = producto
        top = tk.Toplevel(self)
        top.title("Cantidad y precio")
        top.geometry("320x160")
        tk.Label(top, text=f"Ingrese cantidad para {nombre}:").pack(pady=6)
        entry_qty = tk.Entry(top)
        entry_qty.pack()
        tk.Label(top, text="Precio unitario (opcional):").pack(pady=6)
        entry_price = tk.Entry(top)
        entry_price.pack()
        tk.Button(top, text="Aceptar", command=lambda: self._confirm_qty(top, entry_qty, entry_price, producto)).pack(pady=8)

    def _confirm_qty(self, win, entry_qty, entry_price, producto):
        try:
            qty = int(entry_qty.get())
            if qty <= 0:
                raise ValueError
        except Exception:
            mb.showerror("Error", "Cantidad inválida")
            return
        try:
            price = float(entry_price.get()) if entry_price.get().strip() else 0.0
        except Exception:
            mb.showerror("Error", "Precio inválido")
            return
        win.destroy()
        cdb, nombre, stock, umbral = producto
        self.reponer.append((cdb, nombre, qty, price))
        mb.showinfo("Añadido", f"Agregado {qty} unidades de {nombre}")

    def _guardar_reposicion(self):
        if not self.reponer:
            mb.showwarning("Reposición", "No hay productos para reponer")
            return
        fecha = datetime.now().isoformat()
        conn = sqlite3.connect(self.db)
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO reposicion (fecha) VALUES (?)", (fecha,))
            rid = cur.lastrowid
            total = 0
            for cdb, nombre, qty, price in self.reponer:
                cur.execute("INSERT INTO reposicion_detalle (reposicion, cdb, cantidad, precio_compra) VALUES (?, ?, ?, ?)",
                            (rid, cdb, qty, price))
                cur.execute("UPDATE producto SET cantidad = cantidad + ? WHERE cdb = ?", (qty, cdb))
                mb.showinfo("Reposición", "Reposición registrada correctamente")
                self.reponer.clear()
                self._load_products()
                try:
                    self.master.master.frames["inventario"].update_contents()
                except Exception:
                    pass
                try:
                    self.master.master.frames["caja"].update_contents()
                except Exception:
                    pass
                try:
                    self.master.master.alert_icon.check_alerts()
                except Exception:
                    pass

                total += price * qty
            # descontar caja
            cur.execute("INSERT OR IGNORE INTO dinero (id, total) VALUES (1,0)")
            cur.execute("UPDATE dinero SET total = total - ? WHERE id=1", (total,))
            conn.commit()
            mb.showinfo("Reposición", "Reposición registrada correctamente")
            self.reponer.clear()
            self._load_products()
            try:
                self.master.master.frames["caja"].update_contents()
            except Exception:
                pass
            try:
                self.master.master.alert_icon.check_alerts()
            except Exception:
                pass
        except Exception as e:
            conn.rollback()
            mb.showerror("Error", str(e))
        finally:
            conn.close()
