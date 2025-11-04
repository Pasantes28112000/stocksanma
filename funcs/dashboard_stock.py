# funcs/dashboard_stock.py
import customtkinter as ctk
import tkinter.messagebox as mb
import sqlite3
from datetime import datetime

class StockFrame(ctk.CTkFrame):
    def __init__(self, parent, db_path):
        super().__init__(parent)
        self.db = db_path
        self._selected = None
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Stock", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(8,12))
        top = ctk.CTkFrame(self)
        top.pack(fill="x", padx=12)
        ctk.CTkButton(top, text="Refrescar", command=self.update_contents).pack(side="left", padx=6)
        ctk.CTkButton(top, text="Agregar", command=self._add_product).pack(side="left", padx=6)
        ctk.CTkButton(top, text="Editar", command=self._edit_product).pack(side="left", padx=6)
        ctk.CTkButton(top, text="Eliminar", command=self._delete_product).pack(side="left", padx=6)

        self.container = ctk.CTkScrollableFrame(self)
        self.container.pack(fill="both", expand=True, padx=12, pady=12)

    def update_contents(self):
        for w in self.container.winfo_children():
            w.destroy()
        conn = sqlite3.connect(self.db)
        cur = conn.cursor()
        cur.execute("SELECT cdb, nombre, precio, cantidad, margen, umbral, perecedero FROM producto ORDER BY nombre")
        rows = cur.fetchall()
        conn.close()
        hdr = ctk.CTkLabel(self.container, text=f"{'CDB':<8}{'Nombre':<30}{'Precio':>10}{'Cant':>8}{'Umbral':>8}{'P':>3}", anchor="w")
        hdr.pack(anchor="w", padx=6, pady=(4,2))
        for r in rows:
            cdb, nombre, precio, cantidad, margen, umbral, perecedero = r
            txt = f"{str(cdb):<8}{nombre[:28]:<30}{precio:10.2f}{cantidad:8d}{umbral:8d}{'Y' if perecedero else 'N':>3}"
            lbl = ctk.CTkLabel(self.container, text=txt, anchor="w")
            lbl.pack(fill="x", padx=6, pady=2)
            lbl.bind("<Button-1>", lambda e, id=cdb: self._select(id))

    def _select(self, cdb):
        self._selected = cdb
        # visual feedback: re-render and mark selection
        for w in self.container.winfo_children():
            # cheap: change text_color on the matching label
            try:
                text = w.cget("text")
                if text.startswith(str(cdb)):
                    w.configure(text_color="#00FF00")
                else:
                    w.configure(text_color=None)
            except Exception:
                pass

    def _add_product(self):
        dlg = ProductEditor(self, self.db, None, on_save=self.update_contents)
        dlg.open()

    def _edit_product(self):
        if not self._selected:
            mb.showwarning("Seleccionar", "Seleccione un producto haciendo click sobre él")
            return
        dlg = ProductEditor(self, self.db, self._selected, on_save=self.update_contents)
        dlg.open()

    def _delete_product(self):
        if not self._selected:
            mb.showwarning("Seleccionar", "Seleccione un producto")
            return
        if not mb.askyesno("Confirmar", "Eliminar producto seleccionado?"):
            return
        conn = sqlite3.connect(self.db)
        cur = conn.cursor()
        cur.execute("DELETE FROM producto WHERE cdb=?", (self._selected,))
        conn.commit()
        conn.close()
        self._selected = None
        mb.showinfo("Eliminado", "Producto eliminado")
        self.update_contents()

class ProductEditor(ctk.CTkToplevel):
    def __init__(self, parent, db_path, cdb=None, on_save=None):
        super().__init__(parent)
        self.db = db_path
        self.cdb = cdb
        self.on_save = on_save
        self.title("Producto")
        self.geometry("460x360")
        self._build()

    def _build(self):
        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        self.entries = {}
        labels = [("Código (CDB)", "cdb"), ("Nombre", "nombre"), ("Precio", "precio"), ("Cantidad", "cantidad"), ("Umbral", "umbral"), ("Margen (ej:0.2)", "margen")]
        for i, (lab, key) in enumerate(labels):
            ctk.CTkLabel(frame, text=lab).grid(row=i, column=0, sticky="w", pady=6)
            ent = ctk.CTkEntry(frame)
            ent.grid(row=i, column=1, padx=6, pady=6)
            self.entries[key] = ent
        self.perec = ctk.CTkCheckBox(frame, text="Perecedero")
        self.perec.grid(row=len(labels), column=0, columnspan=2, pady=6)
        ctk.CTkButton(frame, text="Guardar", command=self.save).grid(row=len(labels)+1, column=0, columnspan=2, pady=12)

        if self.cdb:
            conn = sqlite3.connect(self.db)
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
                if perecedero:
                    self.perec.select()
                else:
                    self.perec.deselect()

    def open(self):
        self.grab_set()

    def save(self):
        try:
            cdb_text = self.entries["cdb"].get()
            cdb = int(cdb_text)
            nombre = self.entries["nombre"].get().strip()
            precio = float(self.entries["precio"].get() or 0)
            cantidad = int(self.entries["cantidad"].get() or 0)
            umbral = int(self.entries["umbral"].get() or 0)
            margen = float(self.entries["margen"].get() or 0.2)
            perec = 1 if self.perec.get() else 0
            conn = sqlite3.connect(self.db)
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
            mb.showinfo("Guardado", "Producto guardado correctamente")
        except Exception as e:
            mb.showerror("Error", str(e))
