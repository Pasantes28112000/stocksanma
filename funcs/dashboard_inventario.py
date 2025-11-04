# funcs/dashboard_inventario.py
import customtkinter as ctk
import tkinter as tk
import tkinter.messagebox as mb
import sqlite3
from lib_db import load_config
import os
from PIL import Image
import barcode
from barcode.writer import ImageWriter
from customtkinter import CTkImage


class InventarioFrame(ctk.CTkFrame):
    def __init__(self, parent, db_path, config):
        super().__init__(parent)
        self.db = db_path
        self.config = config or load_config()
        self.selected = set()
        self._default_text_color = None
        self._build_ui()
        self._refresh_table()

    def _build_ui(self):
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(header, text="Inventario", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")
        self.search = ctk.CTkEntry(header, placeholder_text="Buscar por nombre o CDB")
        self.search.pack(side="left", padx=8)
        self.search.bind("<KeyRelease>", lambda e: self._refresh_table())

        btns = ctk.CTkFrame(header)
        btns.pack(side="right")
        ctk.CTkButton(btns, text="Agregar", command=self._open_add).pack(side="left", padx=4)
        ctk.CTkButton(btns, text="Editar", command=self._edit_selected).pack(side="left", padx=4)
        ctk.CTkButton(btns, text="Eliminar seleccionados", fg_color="#f44336", command=self._delete_selected).pack(side="left", padx=4)
        ctk.CTkButton(btns, text="Refrescar", command=self._refresh_table).pack(side="left", padx=4)

        self.table = ctk.CTkScrollableFrame(self)
        self.table.pack(fill="both", expand=True, padx=10, pady=8)
        self.rows = []

    def update_contents(self):
        self._refresh_table()

    def _refresh_table(self):
        for w in self.table.winfo_children():
            w.destroy()
        self.rows.clear()
        self.selected.clear()

        q = self.search.get().strip().lower()
        conn = sqlite3.connect(self.db)
        cur = conn.cursor()
        cur.execute("SELECT cdb, nombre, precio, cantidad, umbral, perecedero FROM producto ORDER BY nombre")
        rows = cur.fetchall()
        conn.close()

        moneda = (self.config or load_config()).get("moneda", "$")
        iva_pct = (self.config or load_config()).get("iva", 21) / 100.0

        hdr = ctk.CTkLabel(self.table, text=f"{'CDB':<8}{'Nombre':<30}{'Precio':>12}{'Stock':>8}{'Umbral':>8}{'P':>3}")
        hdr.pack(anchor="w", padx=6, pady=(6, 4))

        for idx, r in enumerate(rows):
            cdb, nombre, precio, cantidad, umbral, perec = r
            if q and q not in str(cdb).lower() and q not in (nombre or "").lower():
                continue
            precio_con_iva = precio * (1 + iva_pct)
            text = f"{str(cdb):<8}{nombre[:28]:<30}{moneda}{precio_con_iva:>9.2f}{cantidad:>8}{umbral:>8}{'Y' if perec else 'N'}"
            lbl = ctk.CTkLabel(self.table, text=text, anchor="w")
            lbl.pack(fill="x", padx=6, pady=2)
            if self._default_text_color is None:
                try:
                    self._default_text_color = lbl.cget("text_color")
                except Exception:
                    self._default_text_color = None
            lbl.bind("<Button-1>", lambda e, cdb=cdb, lbl=lbl: self._toggle_select(cdb, lbl))
            self.rows.append((cdb, lbl))

    def _toggle_select(self, cdb, lbl):
        

        if cdb in self.selected:
            self.selected.remove(cdb)
            lbl.configure(text_color=self._default_text_color)
        else:
            self.selected.add(cdb)
            lbl.configure(text_color="green")
            

    def _open_add(self):
        AddEditDialog(self, self.db, mode="add", on_save=self._refresh_table).open()

    def _edit_selected(self):
        if len(self.selected) != 1:
            mb.showwarning("Editar", "Seleccione un único producto para editar.")
            return
        cdb = next(iter(self.selected))
        AddEditDialog(self, self.db, mode="edit", cdb=cdb, on_save=self._refresh_table).open()

    def _delete_selected(self):
        if not self.selected:
            mb.showwarning("Eliminar", "Seleccione al menos un producto")
            return
        if not mb.askyesno("Confirmar", f"Eliminar {len(self.selected)} producto(s)?"):
            return
        conn = sqlite3.connect(self.db)
        cur = conn.cursor()
        try:
            for cdb in list(self.selected):
                cur.execute("DELETE FROM producto WHERE cdb=?", (cdb,))
            conn.commit()
            mb.showinfo("Eliminado", f"{len(self.selected)} producto(s) eliminados")
            self._refresh_table()
        except Exception as e:
            conn.rollback()
            mb.showerror("Error", str(e))
        finally:
            conn.close()


class AddEditDialog(ctk.CTkToplevel):
    def __init__(self, parent, db, mode="add", cdb=None, on_save=None):
        super().__init__(parent)
        self.parent = parent
        self.db = db
        self.mode = mode
        self.cdb = cdb
        self.on_save = on_save
        self.title("Agregar producto" if mode == "add" else f"Editar {cdb}")
        self.geometry("480x340")
        self.transient(parent)
        self.grab_set()
        self._build()
        if mode == "edit":
            self._load()
    def _mostrar_barcode(self, cdb):
        """Muestra el código de barras si existe como imagen en data/barcodes/"""
        import os, io
        from PIL import Image
        from customtkinter import CTkImage, CTkLabel

        path = os.path.join("data", "barcodes", f"{cdb}.png")
        if not os.path.exists(path):
            return  # No hay código para este producto

        # Cargar imagen en memoria
        with open(path, "rb") as f:
            data = io.BytesIO(f.read())
        self.img = Image.open(data)
        self.img.load()

        # Crear imagen CTk y label
        barcode_img = CTkImage(light_image=self.img, dark_image=self.img, size=(280, 90))
        self.barcode_label = CTkLabel(self, image=barcode_img, text="")
        self.barcode_label.image = barcode_img  # mantener referencia
        self.barcode_label.pack(pady=(10, 5))

    def _build(self):
        frm = ctk.CTkFrame(self)
        frm.pack(fill="both", expand=True, padx=12, pady=12)

        ctk.CTkLabel(frm, text="CDB (num)").grid(row=0, column=0, sticky="w")
        self.e_cdb = ctk.CTkEntry(frm)
        self.e_cdb.grid(row=0, column=1, pady=6)

        ctk.CTkLabel(frm, text="Nombre").grid(row=1, column=0, sticky="w")
        self.e_nombre = ctk.CTkEntry(frm)
        self.e_nombre.grid(row=1, column=1, pady=6)

        ctk.CTkLabel(frm, text="Stock").grid(row=2, column=0, sticky="w")
        self.e_stock = ctk.CTkEntry(frm)
        self.e_stock.grid(row=2, column=1, pady=6)

        ctk.CTkLabel(frm, text="Precio (sin IVA)").grid(row=3, column=0, sticky="w")
        self.e_precio = ctk.CTkEntry(frm)
        self.e_precio.grid(row=3, column=1, pady=6)

        ctk.CTkLabel(frm, text="Umbral").grid(row=4, column=0, sticky="w")
        self.e_umbral = ctk.CTkEntry(frm)
        self.e_umbral.grid(row=4, column=1, pady=6)

        self.perec_var = tk.IntVar(value=0)
        tk.Checkbutton(frm, text="Perecedero", variable=self.perec_var).grid(row=5, column=1, sticky="w", pady=6)

        text_btn = "Guardar" if self.mode == "add" else "Guardar cambios"
        ctk.CTkButton(frm, text=text_btn, command=self._save).grid(row=6, column=0, columnspan=2, pady=12)

    def _load(self):
        conn = sqlite3.connect(self.db)
        cur = conn.cursor()
        cur.execute("SELECT cdb, nombre, precio, cantidad, umbral, perecedero FROM producto WHERE cdb=?", (self.cdb,))
        r = cur.fetchone()
        conn.close()
        if not r:
            mb.showerror("Error", "Producto no encontrado")
            self.destroy()
            return
        cdb, nombre, precio, cantidad, umbral, perec = r
        self.e_cdb.insert(0, str(cdb))
        self.e_cdb.configure(state="disabled")
        self.e_nombre.insert(0, nombre)
        self.e_stock.insert(0, str(cantidad))
        self.e_precio.insert(0, str(precio))
        self.e_umbral.insert(0, str(umbral))
        self.perec_var.set(perec or 0)

        self._mostrar_barcode(cdb)


    def _save(self):
        try:
            cdb = int(self.e_cdb.get().strip())
            nombre = self.e_nombre.get().strip()
            cantidad = int(self.e_stock.get().strip() or 0)
            precio = float(self.e_precio.get().strip() or 0.0)
            umbral = int(self.e_umbral.get().strip() or 0)
            perec = int(self.perec_var.get())
        except Exception:
            mb.showerror("Error", "Revise los campos numéricos")
            return

        conn = sqlite3.connect(self.db)
        cur = conn.cursor()
        try:
            if self.mode == "add":
                cur.execute(
                    "INSERT INTO producto (cdb, nombre, precio, cantidad, umbral, perecedero) VALUES (?,?,?,?,?,?)",
                    (cdb, nombre, precio, cantidad, umbral, perec))
            else:
                cur.execute(
                    "UPDATE producto SET nombre=?, precio=?, cantidad=?, umbral=?, perecedero=? WHERE cdb=?",
                    (nombre, precio, cantidad, umbral, perec, cdb))
            conn.commit()
            if self.on_save:
                self.on_save()
            mb.showinfo("Guardado", "Producto guardado correctamente")
            self.destroy()
        except sqlite3.IntegrityError:
            conn.rollback()
            mb.showerror("Error", "CDB ya existe")
        except Exception as e:
            conn.rollback()
            mb.showerror("Error", str(e))
        finally:
            conn.close()

    def open(self):
        self.grab_set()
