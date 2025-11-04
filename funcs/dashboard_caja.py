# funcs/dashboard_caja.py
import customtkinter as ctk
import sqlite3
import tkinter.messagebox as mb
from lib_db import load_config

class CajaFrame(ctk.CTkFrame):
    def __init__(self, parent, db_path, config=None):
        super().__init__(parent)
        self.db = db_path
        self.config = config or load_config()
        self._build_ui()
        self.update_contents()

    def _build_ui(self):
        header = ctk.CTkLabel(self, text="Caja y Movimientos", font=ctk.CTkFont(size=18, weight="bold"))
        header.pack(pady=8)

        top = ctk.CTkFrame(self)
        top.pack(fill="x", padx=10, pady=6)
        ctk.CTkLabel(top, text="Total en caja").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        self.total_var = ctk.StringVar(value="0.00")
        self.e_total = ctk.CTkEntry(top, textvariable=self.total_var, width=160)
        self.e_total.grid(row=0, column=1, padx=6, pady=6)
        ctk.CTkButton(top, text="Actualizar", command=self.update_contents).grid(row=0, column=2, padx=6)
        ctk.CTkButton(top, text="Agregar ingreso extra", command=self._add_extra).grid(row=0, column=3, padx=6)

        filter_frame = ctk.CTkFrame(self)
        filter_frame.pack(fill="x", padx=10, pady=6)
        ctk.CTkLabel(filter_frame, text="Desde (YYYY-MM-DD)").grid(row=0, column=0, padx=6, pady=4)
        self.e_desde = ctk.CTkEntry(filter_frame, width=120)
        self.e_desde.grid(row=0, column=1, padx=6)
        ctk.CTkLabel(filter_frame, text="Hasta").grid(row=0, column=2, padx=6)
        self.e_hasta = ctk.CTkEntry(filter_frame, width=120)
        self.e_hasta.grid(row=0, column=3, padx=6)
        ctk.CTkLabel(filter_frame, text="CDB o Nombre").grid(row=1, column=0, padx=6)
        self.e_filtro = ctk.CTkEntry(filter_frame, width=240)
        self.e_filtro.grid(row=1, column=1, columnspan=2, padx=6)
        ctk.CTkButton(filter_frame, text="Buscar", command=self.load_movements).grid(row=1, column=3, padx=6)

        self.moves_list = ctk.CTkScrollableFrame(self)
        self.moves_list.pack(fill="both", expand=True, padx=10, pady=6)

    def update_contents(self):
        conn = sqlite3.connect(self.db)
        cur = conn.cursor()
        cur.execute("SELECT total FROM dinero WHERE id=1")
        row = cur.fetchone()
        conn.close()
        symbol = (self.config or load_config()).get("moneda", "$")
        if row:
            self.total_var.set(f"{symbol}{row[0]:.2f}")
        else:
            self.total_var.set(f"{symbol}0.00")
        # refresh movements view with current filters
        self.load_movements()

    def _add_extra(self):
        import tkinter.simpledialog as sd
        monto = sd.askfloat("Ingreso extra", "Monto del ingreso:")
        if monto is None:
            return
        desc = sd.askstring("Descripción", "Descripción del ingreso (opcional):") or "Ingreso manual"
        conn = sqlite3.connect(self.db)
        cur = conn.cursor()
        try:
            cur.execute("INSERT OR IGNORE INTO dinero (id, total) VALUES (1,0)")
            cur.execute("UPDATE dinero SET total = total + ? WHERE id=1", (monto,))
            # add a reposicion-like record as movement
            cur.execute("INSERT INTO reposicion (fecha) VALUES (datetime('now'))")
            rid = cur.lastrowid
            cur.execute("INSERT INTO reposicion_detalle (reposicion, cdb, cantidad, precio_compra) VALUES (?, ?, ?, ?)",
                        (rid, 0, 0, monto))
            conn.commit()
            mb.showinfo("Ingreso", "Ingreso registrado")
            self.update_contents()
            try:
                self.master.master.alert_icon.check_alerts()
            except Exception:
                pass
        except Exception as e:
            conn.rollback()
            mb.showerror("Error", str(e))
        finally:
            conn.close()

    def load_movements(self):
        desde = self.e_desde.get().strip()
        hasta = self.e_hasta.get().strip()
        filtro = self.e_filtro.get().strip().lower()

        conn = sqlite3.connect(self.db)
        cur = conn.cursor()
        cur.execute("""
            SELECT v.id, v.fecha, vd.cdb, p.nombre, vd.cantidad, vd.precio_venta, 'Venta'
            FROM venta v
            JOIN venta_detalle vd ON v.id = vd.venta
            LEFT JOIN producto p ON p.cdb = vd.cdb
            UNION ALL
            SELECT r.id, r.fecha, rd.cdb, p.nombre, rd.cantidad, rd.precio_compra, 'Reposición'
            FROM reposicion r
            JOIN reposicion_detalle rd ON r.id = rd.reposicion
            LEFT JOIN producto p ON p.cdb = rd.cdb
            ORDER BY fecha DESC
        """)
        rows = cur.fetchall()
        conn.close()

        def keep(row):
            _, fecha, cdb, nombre, qty, precio, tipo = row
            if desde and fecha[:10] < desde:
                return False
            if hasta and fecha[:10] > hasta:
                return False
            if filtro:
                if filtro not in str(cdb).lower() and filtro not in (nombre or "").lower():
                    return False
            return True

        rows = [r for r in rows if keep(r)]
        for w in self.moves_list.winfo_children():
            w.destroy()
        symbol = (self.config or load_config()).get("moneda", "$")
        hdr = ctk.CTkLabel(self.moves_list, text=f"{'Tipo':<12}{'Fecha':<20}{'CDB':<8}{'Nombre':<22}{'Cant':<6}{'Precio':<12}")
        hdr.pack(anchor="w", padx=6, pady=(6,4))
        for r in rows:
            _, fecha, cdb, nombre, qty, precio, tipo = r
            ctk.CTkLabel(self.moves_list, text=f"{tipo:<12}{fecha[:19]:<20}{str(cdb):<8}{(nombre or '')[:22]:<22}{str(qty):<6}{symbol}{float(precio):.2f}").pack(anchor="w", padx=6, pady=2)
