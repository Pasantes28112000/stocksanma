# main.py
import customtkinter as ctk
import tkinter.messagebox as mb
from lib_db import init_db
import os

# Import módulos del dashboard
from funcs.dashboard_stock import StockFrame
from funcs.dashboard_venta import VentaFrame
from funcs.dashboard_compra import CompraFrame
from funcs.dashboard_caja import CajaFrame
from funcs.dashboard_vencimientos import VencimientosFrame
from funcs.dashboard_reportes import ReportesFrame
from funcs.dashboard_alertas import AlertasFrame

APP_TITLE = "TecnoDashboard"

class App(ctk.CTk):
    def __init__(self, db_path="data.db"):
        super().__init__()
        self.db_path = db_path
        self.title(APP_TITLE)
        self.geometry("1100x700")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("dark-blue")
        init_db(self.db_path)

        self.grid_columnconfigure(1, weight=1)
        self._create_sidebar()
        self._create_content()

    def _create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nswe")
        self.sidebar.grid_rowconfigure(7, weight=1)

        self.logo = ctk.CTkLabel(self.sidebar, text=APP_TITLE, font=ctk.CTkFont(size=20, weight="bold"))
        self.logo.grid(row=0, column=0, padx=12, pady=12)

        self.btn_dashboard = ctk.CTkButton(self.sidebar, text="Stock", command=lambda: self.show("stock"))
        self.btn_venta = ctk.CTkButton(self.sidebar, text="Venta", command=lambda: self.show("venta"))
        self.btn_compra = ctk.CTkButton(self.sidebar, text="Compra", command=lambda: self.show("compra"))
        self.btn_venc = ctk.CTkButton(self.sidebar, text="Vencimientos", command=lambda: self.show("vencimientos"))
        self.btn_reportes = ctk.CTkButton(self.sidebar, text="Reportes", command=lambda: self.show("reportes"))
        self.btn_alertas = ctk.CTkButton(self.sidebar, text="Alertas", command=lambda: self.show("alertas"))
        self.btn_caja = ctk.CTkButton(self.sidebar, text="Caja", command=lambda: self.show("caja"))

        for i, w in enumerate([self.btn_dashboard, self.btn_venta, self.btn_compra, self.btn_venc, self.btn_reportes, self.btn_alertas, self.btn_caja], start=1):
            w.grid(row=i, column=0, padx=12, pady=6, sticky="we")

        self.appearance = ctk.CTkOptionMenu(self.sidebar, values=["Light", "Dark", "System"], command=self._change_appearance)
        self.appearance.grid(row=8, column=0, padx=12, pady=12, sticky="we")

    def _create_content(self):
        self.container = ctk.CTkFrame(self)
        self.container.grid(row=0, column=1, sticky="nswe", padx=10, pady=10)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # crear instancias de frames
        self.frames = {
            "stock": StockFrame(self.container, self.db_path),
            "venta": VentaFrame(self.container, self.db_path, self._on_alert),
            "compra": CompraFrame(self.container, self.db_path, self._on_alert),
            "caja": CajaFrame(self.container, self.db_path),
            "vencimientos": VencimientosFrame(self.container, self.db_path),
            "reportes": ReportesFrame(self.container, self.db_path),
            "alertas": AlertasFrame(self.container, self.db_path, self._on_alert)
        }
        for f in self.frames.values():
            f.grid(row=0, column=0, sticky="nswe")
        self.show("stock")

    def show(self, key):
        for k, f in self.frames.items():
            if k == key:
                f.update_contents()
                f.lift()
            else:
                f.lower()

    def _change_appearance(self, val):
        if val == "Light":
            ctk.set_appearance_mode("Light")
        elif val == "Dark":
            ctk.set_appearance_mode("Dark")
        else:
            ctk.set_appearance_mode("System")

    def _on_alert(self):
        # método llamado por módulos cuando se necesita refrescar alertas
        try:
            self.frames["alertas"].update_contents()
        except Exception:
            pass

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    db = os.path.join("data", "data.db")
    app = App(db)
    app.mainloop()
