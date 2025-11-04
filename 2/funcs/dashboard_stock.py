import customtkinter as ctk
import tkinter.messagebox as mb
from lib_db import fetch_all_products, get_connection
import sqlite3
from utils import formatting

class StockFrame(ctk.CTkFrame):
    def __init__(self, parent, db_path):
        super().__init__(parent)
        self.db = db_path
        self._selected = None
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
        hdr = ctk.CTkLabel(self.table_frame, text=f"{'CDB':<10}{'Nombre':<35}{'Precio':>12}{'Cant':>8}{'Umbral':>8}{'P':>3}")
        hdr.pack(anchor="w", padx=6, pady=(4,2))
        self.rows = []
        for p in products:
            # desempaquetado seguro
            try:
                cdb, nombre, precio, cantidad, margen, umbral, perecedero = p
            except Exception:
                # fallback si la tupla tiene otro layout
                cdb = p[0]
                nombre = p[1] if len(p) > 1 else ""
                precio = p[2] if len(p) > 2 else 0.0
                cantidad = p[3] if len(p) > 3 else 0
                umbral = p[4] if len(p) > 4 else 0
                perecedero = p[6] if len(p) > 6 else False

            # usar formatting para mostrar precio con símbolo, separadores y decimales
            try:
                precio_txt = formatting.format_amount(precio)
            except Exception:
                precio_txt = f"{precio:.2f}"

            # ajustar campo precio a ancho fijo para que columnas alineen razonablemente
            precio_field = f"{precio_txt:>12}"
            nombre_field = f"{nombre[:32]:<35}"
            txt = f"{str(cdb):<10}{nombre_field}{precio_field}{cantidad:8d}{umbral:8d}{'Y' if perecedero else 'N'}"

            lbl = ctk.CTkLabel(self.table_frame, text=txt, anchor="w")
            lbl.pack(fill="x", padx=6, pady=2)
            # guardar color original por etiqueta para restaurarlo luego
            try:
                orig_color = lbl.cget("text_color")
                if orig_color is None:
                    orig_color = ""  # evitar None, usar cadena vacía como no-op
            except Exception:
                orig_color = ""
            lbl.bind("<Button-1>", lambda e, id=cdb: self._select(id))
            self.rows.append((cdb, lbl, orig_color))
        self._selected = None

    def _select(self, cdb):
        self._selected = cdb
        # highlight selected; restaurar color original en los demás
        for id_, lbl, orig in self.rows:
            try:
                if id_ == cdb:
                    lbl.configure(text_color="green")
                else:
                    # restaurar color original si tenemos uno válido
                    if orig:
                        lbl.configure(text_color=orig)
                    else:
                        # si no hay color original conocido, intentar quitar override usando empty string
                        try:
                            lbl.configure(text_color="")
                        except Exception:
                            pass
            except Exception:
                # no interrumpir si algún configure falla
                pass

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
                # mostrar valor bruto en el entry; la vista principal usa formatting
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