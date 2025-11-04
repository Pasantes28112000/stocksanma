# dashboard_venta.py
import customtkinter as ctk
import tkinter.messagebox as mb
from lib_db import get_connection, fetch_all_products
import datetime

class VentaFrame(ctk.CTkFrame):
    def __init__(self, parent, db_path, on_alert_callback=None):
        super().__init__(parent)
        self.db = db_path
        self.on_alert = on_alert_callback
        self.cart = []
        self.total = 0.0
        self.build()

    def build(self):
        header = ctk.CTkLabel(self, text="Ventas", font=ctk.CTkFont(size=18, weight="bold"))
        header.pack(pady=6)
        top = ctk.CTkFrame(self)
        top.pack(fill="x", padx=12, pady=6)
        ctk.CTkButton(top, text="Añadir producto", command=self._open_add).pack(side="left", padx=6)
        ctk.CTkButton(top, text="Vender", command=self._vender).pack(side="left", padx=6)
        ctk.CTkButton(top, text="Limpiar", command=self._limpiar).pack(side="left", padx=6)

        self.list_frame = ctk.CTkScrollableFrame(self)
        self.list_frame.pack(fill="both", expand=True, padx=12, pady=6)
        self.total_label = ctk.CTkLabel(self, text="Total: $0.00", font=ctk.CTkFont(size=14))
        self.total_label.pack(pady=6)

    def update_contents(self):
        self._render_cart()

    def _render_cart(self):
        for w in self.list_frame.winfo_children():
            w.destroy()
        for idx, item in enumerate(self.cart):
            txt = f"{item['cdb']} - {item['nombre']} x {item['cantidad']} @ {item['precio']:.2f}"
            lbl = ctk.CTkLabel(self.list_frame, text=txt)
            lbl.pack(fill="x", padx=6, pady=3)
            ctk.CTkButton(self.list_frame, text="Eliminar", width=80, command=lambda i=idx: self._remove(i)).pack(padx=6, pady=3)

        self.total_label.configure(text=f"Total: ${self.total:.2f}")

    def _open_add(self):
        dlg = ProductPicker(self, self.db, self._on_added)
        dlg.open()

    def _on_added(self, item):
        # item: dict with cdb, nombre, precio, cantidad
        self.cart.append(item)
        self.total += item['precio'] * item['cantidad']
        self._render_cart()

    def _remove(self, idx):
        item = self.cart.pop(idx)
        self.total -= item['precio'] * item['cantidad']
        self._render_cart()

    def _limpiar(self):
        self.cart = []
        self.total = 0.0
        self._render_cart()

    def _vender(self):
        if not self.cart:
            mb.showwarning("Carrito", "No hay productos en la venta")
            return
        conn = get_connection(self.db)
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO venta (fecha) VALUES (?)", (datetime.datetime.now().isoformat(),))
            vid = cur.lastrowid
            for it in self.cart:
                cdb = int(it['cdb'])
                cant = int(it['cantidad'])
                precio = float(it['precio'])
                # check stock
                cur.execute("SELECT cantidad, precio, margen FROM producto WHERE cdb=?", (cdb,))
                res = cur.fetchone()
                if not res or res[0] < cant:
                    raise ValueError(f"Stock insuficiente para {it['nombre']}")
                nueva = res[0] - cant
                cur.execute("UPDATE producto SET cantidad=? WHERE cdb=?", (nueva, cdb))
                cur.execute("INSERT INTO venta_detalle (venta, cdb, cantidad, precio_venta) VALUES (?, ?, ?, ?)", (vid, cdb, cant, precio))
                # actualiza dinero
                ganancia = cant * precio
                cur.execute("UPDATE dinero SET total = total + ? WHERE id=1", (ganancia,))
            conn.commit()
            mb.showinfo("Venta", "Venta registrada con éxito")
            self._limpiar()
            if self.on_alert:
                self.on_alert()
        except Exception as e:
            conn.rollback()
            mb.showerror("Error", str(e))
        finally:
            conn.close()

class ProductPicker(ctk.CTkToplevel):
    def __init__(self, parent, db, on_select):
        super().__init__(parent)
        self.db = db
        self.on_select = on_select
        self.title("Seleccionar producto")
        self.geometry("560x420")
        self.build()

    def build(self):
        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        self.search = ctk.CTkEntry(frame, placeholder_text="Buscar por nombre o CDB")
        self.search.pack(fill="x", pady=6)
        ctk.CTkButton(frame, text="Buscar", command=self._buscar).pack(pady=6)
        self.results = ctk.CTkScrollableFrame(frame)
        self.results.pack(fill="both", expand=True, pady=6)
        self._buscar()

    def _buscar(self):
        for w in self.results.winfo_children():
            w.destroy()
        q = self.search.get().strip().lower()
        products = fetch_all_products(self.db)
        for p in products:
            cdb, nombre, precio, cantidad, margen, umbral, perecedero = p
            if q and q not in nombre.lower() and q not in str(cdb):
                continue
            row = ctk.CTkFrame(self.results)
            row.pack(fill="x", pady=4, padx=4)
            txt = f"{cdb} - {nombre} (Stock: {cantidad}) - ${precio:.2f}"
            ctk.CTkLabel(row, text=txt).pack(side="left", padx=6)
            ctk.CTkButton(row, text="Agregar", width=90, command=lambda p=p: self._seleccionar(p)).pack(side="right", padx=6)

    def _seleccionar(self, p):
        cdb, nombre, precio, cantidad, margen, umbral, perecedero = p
        # pedir cantidad
        import tkinter.simpledialog as sd
        cantidad = sd.askinteger("Cantidad", f"Ingrese cantidad para {nombre} (stock {p[3]}):", minvalue=1, maxvalue=max(1, p[3]))
        if cantidad:
            item = {'cdb': cdb, 'nombre': nombre, 'precio': precio*(1+margen), 'cantidad': cantidad}
            self.on_select(item)
            self.destroy()

    def open(self):
        self.grab_set()
