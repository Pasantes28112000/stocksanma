# dashboard_stock.py
import customtkinter as ctk
import tkinter.messagebox as mb
from lib_db import fetch_all_products, get_connection
import sqlite3

class StockFrame(ctk.CTkFrame):
    def __init__(self, parent, db_path):
        super().__init__(parent)
        self.db = db_path
        self._build_ui()

    def _build_ui(self):
        header = ctk.CTkLabel(self, text="Stock", font=ctk.CTkFont(size=18, weight="bold"))
        header.pack(pady=(6,12))

        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=12, pady=6)
        ctk.CTkButton(btn_frame, text="Refrescar", command=self.update_contents).pack(side="left", padx=6)
        ctk.CTkButton(btn_frame, text="Agregar", command=self._add_dialog).pack(side="left", padx=6)
        ctk.CTkButton(btn_frame, text="Editar", command=self._edit_selected).pack(side="left", padx=6)
        ctk.CTkButton(btn_frame, text="Eliminar", command=self._delete_selected).pack(side="left", padx=6)

        self.table_frame = ctk.CTkScrollableFrame(self)
        self.table_frame.pack(fill="both", expand=True, padx=12, pady=6)

        # simple list as table
        self.rows = []

    def update_contents(self):
        for w in self.table_frame.winfo_children():
            w.destroy()
        products = fetch_all_products(self.db)
        hdr = ctk.CTkLabel(self.table_frame, text=f"{'CDB':<10}{'Nombre':<35}{'Precio':>8}{'Cant':>8}{'Umbral':>8}{'P':>3}")
        hdr.pack(anchor="w", padx=6, pady=(4,2))
        self.rows = []
        for p in products:
            cdb, nombre, precio, cantidad, margen, umbral, perecedero = p
            txt = f"{str(cdb):<10}{nombre[:32]:<35}{precio:8.2f}{cantidad:8d}{umbral:8d}{'Y' if perecedero else 'N'}"
            lbl = ctk.CTkLabel(self.table_frame, text=txt, anchor="w")
            lbl.pack(fill="x", padx=6, pady=2)
            lbl.bind("<Button-1>", lambda e, id=cdb: self._select(id))
            self.rows.append((cdb, lbl))
        self._selected = None

    def _select(self, cdb):
        self._selected = cdb
        # highlight selected
        for id_, lbl in self.rows:
            if id_ == cdb:
                lbl.configure(text_color="green")
            else:
                lbl.configure(text_color=None)

    def _add_dialog(self):
        dlg = ProductEditor(self, self.db, on_save=self.update_contents)
        dlg.open()

    def _edit_selected(self):
        if not getattr(self, "_selected", None):
            mb.showwarning("Seleccionar", "Seleccione un producto en la lista")
            return
        dlg = ProductEditor(self, self.db, cdb=self._selected, on_save=self.update_contents)
        dlg.open()

    def _delete_selected(self):
        if not getattr(self, "_selected", None):
            mb.showwarning("Seleccionar", "Seleccione un producto en la lista")
            return
        if not mb.askyesno("Confirmar", "Eliminar producto seleccionado?"):
            return
        conn = get_connection(self.db)
        cur = conn.cursor()
        cur.execute("DELETE FROM producto WHERE cdb=?", (self._selected,))
        conn.commit()
        conn.close()
        self.update_contents()

class ProductEditor(ctk.CTkToplevel):
    def __init__(self, parent, db_path, cdb=None, on_save=None):
        super().__init__(parent)
        self.db = db_path
        self.cdb = cdb
        self.on_save = on_save
        self.title("Producto")
        self.geometry("420x320")
        self.build()

    def build(self):
        self.frame = ctk.CTkFrame(self)
        self.frame.pack(fill="both", expand=True, padx=12, pady=12)
        self.entries = {}
        for i,(label, varname) in enumerate([("Código (CDB)", "cdb"), ("Nombre","nombre"), ("Precio","precio"), ("Cantidad","cantidad"), ("Umbral","umbral"), ("Margen","margen")]):
            ctk.CTkLabel(self.frame, text=label).grid(row=i, column=0, sticky="w", pady=6)
            ent = ctk.CTkEntry(self.frame)
            ent.grid(row=i, column=1, padx=6, pady=6)
            self.entries[varname] = ent
        self.perec_var = ctk.CTkCheckBox(self.frame, text="Perecedero")
        self.perec_var.grid(row=6, column=0, columnspan=2, pady=6)
        ctk.CTkButton(self.frame, text="Guardar", command=self.save).grid(row=7, column=0, columnspan=2, pady=12)

        if self.cdb:
            conn = get_connection(self.db)
            cur = conn.cursor()
            cur.execute("SELECT cdb, nombre, precio, cantidad, margen, umbral, perecedero FROM producto WHERE cdb=?", (self.cdb,))
            row = cur.fetchone()
            conn.close()
            if row:
                cdb, nombre, precio, cantidad, margen, umbral, perecedero = row
                self.entries["cdb"].insert(0, str(cdb))
                self.entries["cdb"].configure(state="disabled")
                self.entries["nombre"].insert(0, nombre)
                self.entries["precio"].insert(0, str(precio))
                self.entries["cantidad"].insert(0, str(cantidad))
                self.entries["umbral"].insert(0, str(umbral))
                self.entries["margen"].insert(0, str(margen))
                self.perec_var.select() if perecedero else self.perec_var.deselect()

    def open(self):
        self.grab_set()

    def save(self):
        try:
            cdb = int(self.entries["cdb"].get())
            nombre = self.entries["nombre"].get().strip()
            precio = float(self.entries["precio"].get() or 0)
            cantidad = int(self.entries["cantidad"].get() or 0)
            umbral = int(self.entries["umbral"].get() or 0)
            margen = float(self.entries["margen"].get() or 0.2)
            perec = 1 if self.perec_var.get() else 0

            conn = get_connection(self.db)
            cur = conn.cursor()
            if self.cdb:
                cur.execute("""UPDATE producto SET nombre=?, precio=?, cantidad=?, umbral=?, margen=?, perecedero=? WHERE cdb=?""",
                            (nombre, precio, cantidad, umbral, margen, perec, cdb))
            else:
                cur.execute("""INSERT INTO producto (cdb, nombre, precio, cantidad, umbral, margen, perecedero) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                            (cdb, nombre, precio, cantidad, umbral, margen, perec))
            conn.commit()
            conn.close()
            if self.on_save:
                self.on_save()
            self.destroy()
        except Exception as e:
            mb.showerror("Error", str(e))
