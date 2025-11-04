import customtkinter as ctk
from lib_db import get_connection
from utils import formatting
import datetime

class ReportesFrame(ctk.CTkFrame):
    """
    Reportes - mostrar filas a nivel ítem con columnas:
      Tipo | Fecha | Producto | Precio
    Intenta leer detalles de venta/compra (varias convenciones de tablas/columnas),
    y si no encuentra detalles muestra movimientos genéricos (caja/movimientos).
    """
    def __init__(self, parent, db_path):
        super().__init__(parent)
        self.db = db_path
        self._build_ui()
        self.update_contents()

    def _build_ui(self):
        header = ctk.CTkLabel(self, text="Movimientos / Reportes", font=ctk.CTkFont(size=18, weight="bold"))
        header.pack(pady=(8, 6))

        ctrl = ctk.CTkFrame(self)
        ctrl.pack(fill="x", padx=12, pady=(0,8))

        ctk.CTkLabel(ctrl, text="Buscar:").grid(row=0, column=0, sticky="w", padx=(4,6))
        self.search_var = ctk.StringVar(value="")
        ent = ctk.CTkEntry(ctrl, textvariable=self.search_var)
        ent.grid(row=0, column=1, sticky="we", padx=(0,6))
        ent.bind("<KeyRelease>", lambda e: self.update_contents())

        ctk.CTkLabel(ctrl, text="Desde (YYYY-MM-DD):").grid(row=0, column=2, sticky="w", padx=(6,6))
        self.from_var = ctk.StringVar(value="")
        ctk.CTkEntry(ctrl, textvariable=self.from_var, width=110).grid(row=0, column=3, sticky="w")

        ctk.CTkLabel(ctrl, text="Hasta (YYYY-MM-DD):").grid(row=0, column=4, sticky="w", padx=(6,6))
        self.to_var = ctk.StringVar(value="")
        ctk.CTkEntry(ctrl, textvariable=self.to_var, width=110).grid(row=0, column=5, sticky="w")

        btn = ctk.CTkButton(ctrl, text="Refrescar", command=self.update_contents, width=90)
        btn.grid(row=0, column=6, padx=(8,4))

        ctrl.grid_columnconfigure(1, weight=1)

        # encabezado de columnas fijo
        hdr = ctk.CTkFrame(self)
        hdr.pack(fill="x", padx=12, pady=(6,2))
        font_h = ctk.CTkFont(size=12, weight="bold")
        ctk.CTkLabel(hdr, text="Tipo", width=10, font=font_h).pack(side="left", padx=(6,6))
        ctk.CTkLabel(hdr, text="Fecha", width=20, font=font_h).pack(side="left", padx=(6,6))
        ctk.CTkLabel(hdr, text="Producto", anchor="w", font=font_h).pack(side="left", expand=True, fill="x", padx=(6,6))
        ctk.CTkLabel(hdr, text="Precio", width=14, anchor="e", font=font_h).pack(side="right", padx=(6,12))

        # contenedor de filas
        self.table_frame = ctk.CTkScrollableFrame(self)
        self.table_frame.pack(fill="both", expand=True, padx=12, pady=(0,12))

    def update_contents(self):
        # limpiar
        for w in self.table_frame.winfo_children():
            w.destroy()

        # obtener filas a nivel ítem
        rows = self._fetch_item_rows()

        # filtros
        q = (self.search_var.get() or "").strip().lower()
        f_from = self._parse_date(self.from_var.get())
        f_to = self._parse_date(self.to_var.get())

        filtered = []
        for tipo, fecha, producto, precio in rows:
            dt = self._ensure_datetime(fecha)
            if f_from and dt and dt < f_from:
                continue
            if f_to and dt and dt > f_to:
                continue
            if q:
                hay = (str(tipo).lower() + " " + str(producto).lower())
                if q not in hay:
                    continue
            filtered.append((tipo, dt, producto, precio))

        if not filtered:
            ctk.CTkLabel(self.table_frame, text="No hay movimientos para mostrar.", font=ctk.CTkFont(size=12)).pack(padx=12, pady=12)
            return

        # mostrar filas
        for i, (tipo, dt, producto, precio) in enumerate(filtered):
            bg = "#f6f7fb" if i % 2 == 0 else "#ffffff"
            row = ctk.CTkFrame(self.table_frame, fg_color=bg, corner_radius=6)
            row.pack(fill="x", padx=6, pady=4)

            fecha_txt = dt.strftime("%Y-%m-%d %H:%M") if isinstance(dt, datetime.datetime) else str(dt or "")
            ctk.CTkLabel(row, text=str(tipo), width=10).pack(side="left", padx=(8,6))
            ctk.CTkLabel(row, text=fecha_txt, width=20).pack(side="left", padx=(6,6))
            ctk.CTkLabel(row, text=str(producto), anchor="w").pack(side="left", expand=True, fill="x", padx=(6,6))
            try:
                txt = formatting.format_amount(precio)
            except Exception:
                try:
                    txt = f"{float(precio):.2f}"
                except Exception:
                    txt = str(precio)
            ctk.CTkLabel(row, text=txt, width=14, anchor="e").pack(side="right", padx=(6,12))

    def _fetch_item_rows(self):
        """
        Devuelve lista de tuplas (tipo, fecha, producto, precio) intentando extraer
        líneas de venta/compra. Si no hay detalles, agrega movimientos de caja/movimientos.
        """
        conn = get_connection(self.db)
        cur = conn.cursor()
        result = []

        try:
            # primero intentar ventas con detalle
            # probamos varias convenciones de tabla/columna
            venta_detail_tables = ["venta_detalle", "detalle_venta", "venta_items", "venta_item", "detalleventa"]
            venta_id_cols = ["venta_id", "id_venta", "venta", "fk_venta"]
            for tbl in venta_detail_tables:
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND lower(name)=?", (tbl.lower(),))
                if cur.fetchone():
                    # intentar columnas comunes
                    for idcol in venta_id_cols:
                        try:
                            sql = f"SELECT v.fecha, COALESCE(p.nombre, vd.nombre, vd.descripcion, '') as producto, " \
                                  f"COALESCE(vd.precio, vd.precio_unitario, vd.unit_price, vd.valor, vd.importe, vd.total) as precio " \
                                  f"FROM {tbl} vd JOIN venta v ON v.id=vd.{idcol} LEFT JOIN producto p ON p.cdb=vd.producto_id"
                            cur.execute(sql)
                            rows = cur.fetchall()
                            if rows:
                                for fecha, producto, precio in rows:
                                    result.append(("Venta", fecha, producto or "", precio or 0.0))
                                break
                        except Exception:
                            continue
                    if result:
                        break

            # luego compras con detalle
            compra_detail_tables = ["compra_detalle", "detalle_compra", "compra_items", "compra_item", "detallecompra"]
            compra_id_cols = ["compra_id", "id_compra", "compra", "fk_compra"]
            for tbl in compra_detail_tables:
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND lower(name)=?", (tbl.lower(),))
                if cur.fetchone():
                    for idcol in compra_id_cols:
                        try:
                            sql = f"SELECT c.fecha, COALESCE(p.nombre, cd.nombre, cd.descripcion, '') as producto, " \
                                  f"COALESCE(cd.precio, cd.precio_unitario, cd.unit_price, cd.valor, cd.importe, cd.total) as precio " \
                                  f"FROM {tbl} cd JOIN compra c ON c.id=cd.{idcol} LEFT JOIN producto p ON p.cdb=cd.producto_id"
                            cur.execute(sql)
                            rows = cur.fetchall()
                            if rows:
                                for fecha, producto, precio in rows:
                                    result.append(("Compra", fecha, producto or "", precio or 0.0))
                                break
                        except Exception:
                            continue
                    if result:
                        break

            # si no se encontraron detalles, caer a movimientos/resumen por venta/compra
            if not result:
                # consultar ventas resumen
                try:
                    cur.execute("SELECT fecha, COALESCE(detalle, descripcion, '') as producto, COALESCE(total, monto, 0) as precio FROM venta")
                    rows = cur.fetchall()
                    for fecha, producto, precio in rows:
                        result.append(("Venta", fecha, producto or "", precio or 0.0))
                except Exception:
                    pass
                # consultar compras resumen
                try:
                    cur.execute("SELECT fecha, COALESCE(detalle, descripcion, proveedor, '') as producto, COALESCE(total, monto, 0) as precio FROM compra")
                    rows = cur.fetchall()
                    for fecha, producto, precio in rows:
                        result.append(("Compra", fecha, producto or "", precio or 0.0))
                except Exception:
                    pass

            # agregar movimientos de caja/movimientos como último recurso
            try:
                cur.execute("SELECT fecha, COALESCE(descripcion, detalle, '') as producto, COALESCE(monto, total, 0) as precio FROM caja")
                for fecha, producto, precio in cur.fetchall():
                    result.append(("Caja", fecha, producto or "", precio or 0.0))
            except Exception:
                pass
            try:
                cur.execute("SELECT fecha, COALESCE(descripcion, detalle, '') as producto, COALESCE(monto, total, 0) as precio FROM movimientos")
                for fecha, producto, precio in cur.fetchall():
                    result.append(("Movimiento", fecha, producto or "", precio or 0.0))
            except Exception:
                pass

        finally:
            try:
                conn.close()
            except Exception:
                pass

        # ordenar por fecha descendente (filas sin fecha al final)
        def _key(row):
            try:
                dt = self._ensure_datetime(row[1])
                return dt.timestamp() if dt else 0
            except Exception:
                return 0

        result.sort(key=_key, reverse=True)
        return result

    def _parse_date(self, text):
        text = (text or "").strip()
        if not text:
            return None
        try:
            return datetime.datetime.fromisoformat(text)
        except Exception:
            try:
                return datetime.datetime.strptime(text, "%Y-%m-%d")
            except Exception:
                return None

    def _ensure_datetime(self, value):
        if value is None:
            return None
        if isinstance(value, datetime.datetime):
            return value
        try:
            return datetime.datetime.fromisoformat(str(value))
        except Exception:
            try:
                return datetime.datetime.strptime(str(value), "%Y-%m-%d %H:%M:%S")
            except Exception:
                try:
                    return datetime.datetime.strptime(str(value), "%Y-%m-%d")
                except Exception:
                    return None