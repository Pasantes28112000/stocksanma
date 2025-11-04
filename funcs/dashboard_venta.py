# funcs/dashboard_venta.py
import tkinter as tk
import customtkinter as ctk
import sqlite3
from datetime import datetime
from lib_db import load_config
import tkinter.messagebox as mb

class VentaFrame(ctk.CTkFrame):
    def __init__(self, parent, db_path, config=None):
        super().__init__(parent)
        self.db = db_path
        self.config = config or load_config()
        self.cart = []
        self._build()
        self.load_products()

    def _build(self):
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(header, text="Ventas", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")
        self.search_entry = ctk.CTkEntry(header, placeholder_text="Buscar nombre o CDB")
        self.search_entry.pack(side="left", padx=8)
        self.search_entry.bind("<KeyRelease>", lambda e: self.load_products())

        body = tk.Frame(self)
        body.pack(fill="both", expand=True, padx=10, pady=6)

        left = tk.Frame(body)
        left.pack(side="left", fill="both", expand=True)
        self.lb_products = tk.Listbox(left)
        self.lb_products.pack(fill="both", expand=True)
        self.lb_products.bind("<Double-Button-1>", lambda e: self._add_selected_to_cart())
        scroll = tk.Scrollbar(left, command=self.lb_products.yview)
        scroll.pack(side="right", fill="y")
        self.lb_products.config(yscrollcommand=scroll.set)

        mid = tk.Frame(body, width=220)
        mid.pack(side="left", fill="y", padx=8)
        tk.Label(mid, text="Cantidad:").pack(pady=(8,2))
        self.e_qty = tk.Entry(mid)
        self.e_qty.pack()
        tk.Label(mid, text="Descuento % (opcional):").pack(pady=(8,2))
        self.e_disc = tk.Entry(mid)
        self.e_disc.pack()
        tk.Button(mid, text="Agregar al carrito", bg="#4CAF50", fg="white", command=self._add_selected_to_cart).pack(pady=10, fill="x")
        tk.Button(mid, text="Quitar último", bg="#f57c00", fg="white", command=self._remove_last).pack(pady=6, fill="x")
        tk.Button(mid, text="Finalizar venta", bg="#2196F3", fg="white", command=self._finalize).pack(pady=10, fill="x")

        right = tk.Frame(body)
        right.pack(side="left", fill="both", expand=True)
        tk.Label(right, text="Carrito").pack(anchor="w")
        self.lb_cart = tk.Listbox(right)
        self.lb_cart.pack(fill="both", expand=True)

        self.total_label = tk.Label(self, text="Total: $0.00", font=("Arial", 12, "bold"))
        self.total_label.pack(anchor="e", padx=12, pady=8)

    def load_products(self):
        q = self.search_entry.get().strip().lower()
        conn = sqlite3.connect(self.db)
        cur = conn.cursor()
        cur.execute("SELECT cdb, nombre, cantidad, precio FROM producto ORDER BY nombre")
        rows = cur.fetchall()
        conn.close()
        self.products = [r for r in rows if not q or (q in str(r[0]).lower()) or (q in (r[1] or "").lower())]
        self.lb_products.delete(0, tk.END)
        cfg = load_config()
        symbol = cfg.get("moneda", "$")
        iva_pct = cfg.get("iva", 21) / 100.0
        for r in self.products:
            cdb, nombre, stock, precio = r
            price_disp = precio * (1 + iva_pct)
            self.lb_products.insert(tk.END, f"{cdb} - {nombre[:30]:30} | Stock: {stock} | {symbol}{price_disp:>8.2f}")

    def _get_selected_product(self):
        sel = self.lb_products.curselection()
        if not sel: return None
        idx = sel[0]
        if idx >= len(self.products): return None
        return self.products[idx]

    def _add_selected_to_cart(self):
        prod = self._get_selected_product()
        if not prod:
            mb.showwarning("Seleccionar", "Seleccione un producto")
            return
        try:
            qty = int(self.e_qty.get().strip() or 1)
            if qty <= 0: raise ValueError
        except Exception:
            mb.showerror("Error", "Cantidad inválida")
            return
        try:
            disc = float(self.e_disc.get().strip() or 0.0)
            if disc < 0: raise ValueError
        except Exception:
            mb.showerror("Error", "Descuento inválido")
            return
        cdb, nombre, stock, precio = prod
        if qty > stock:
            mb.showerror("Error", f"Stock insuficiente (hay {stock})")
            return
        iva_pct = load_config().get("iva", 21) / 100.0
        unit_price = precio * (1 + iva_pct)
        subtotal = unit_price * qty * (1 - disc/100.0)
        self.cart.append({"cdb": cdb, "nombre": nombre, "qty": qty, "unit": unit_price, "subtotal": subtotal})
        self._render_cart()
        self.e_qty.delete(0, tk.END)
        self.e_disc.delete(0, tk.END)

    def _render_cart(self):
        self.lb_cart.delete(0, tk.END)
        total = 0
        symbol = load_config().get("moneda", "$")
        for it in self.cart:
            self.lb_cart.insert(tk.END, f"{it['cdb']} {it['nombre'][:20]:20} x{it['qty']} {symbol}{it['subtotal']:.2f}")
            total += it['subtotal']
        self.total_label.config(text=f"Total: {symbol}{total:.2f}")

    def _remove_last(self):
        if not self.cart: return
        self.cart.pop()
        self._render_cart()

    def _finalize(self):
        if not self.cart:
            mb.showwarning("Carrito", "Carrito vacío")
            return
        # Check stock again from DB to avoid negative stock if concurrent changes
        conn = sqlite3.connect(self.db)
        cur = conn.cursor()
        try:
            for it in self.cart:
                cur.execute("SELECT cantidad FROM producto WHERE cdb=?", (it["cdb"],))
                row = cur.fetchone()
                if not row:
                    raise ValueError(f"Producto {it['nombre']} inexistente")
                if row[0] < it["qty"]:
                    raise ValueError(f"Stock insuficiente para {it['nombre']} (hay {row[0]})")
            # all OK -> create sale
            fecha = datetime.now().isoformat()
            cur.execute("INSERT INTO venta (fecha) VALUES (?)", (fecha,))
            vid = cur.lastrowid
            total = 0
            iva_pct = load_config().get("iva", 21) / 100.0
            for it in self.cart:
                # store price_venta as unit price without doubling IVA
                unit_without_iva = it["unit"] / (1 + iva_pct)
                cur.execute("INSERT INTO venta_detalle (venta, cdb, cantidad, precio_venta) VALUES (?, ?, ?, ?)",
                            (vid, it["cdb"], it["qty"], unit_without_iva))
                cur.execute("UPDATE producto SET cantidad = cantidad - ? WHERE cdb = ?", (it["qty"], it["cdb"]))
                total += it["subtotal"]
            cur.execute("INSERT OR IGNORE INTO dinero (id, total) VALUES (1, 0)")
            cur.execute("UPDATE dinero SET total = total + ? WHERE id=1", (total,))
            conn.commit()
            mb.showinfo("Venta", f"Venta registrada: {load_config().get('moneda','$')}{total:.2f}")
            self.cart.clear()
            self._render_cart()
            self.load_products()
            # update caja and alerts
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

    def update_contents(self):
        self.load_products()
