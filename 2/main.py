import customtkinter as ctk
import tkinter.messagebox as mb
import os
from lib_db import init_db
# Import módulos del dashboard
from funcs.dashboard_stock import StockFrame
from funcs.dashboard_venta import VentaFrame
from funcs.dashboard_compra import CompraFrame
from funcs.dashboard_caja import CajaFrame
from funcs.dashboard_vencimientos import VencimientosFrame
from funcs.dashboard_reportes import ReportesFrame
from funcs.dashboard_alertas import AlertasFrame
from utils import preferences

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

        # cargar preferencias desde el módulo centralizado
        self.prefs = preferences.load()
        try:
            preferences.apply(self.prefs, persist=False)
        except Exception:
            pass

        # layout principal y creación de UI
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

        # quitar selector de apariencia de la barra lateral (se gestiona en Configuración)
        # botón de configuración
        self.btn_settings = ctk.CTkButton(self.sidebar, text="Configuración", command=self._open_settings)
        self.btn_settings.grid(row=8, column=0, padx=12, pady=(0,12), sticky="we")

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
                try:
                    f.update_contents()
                except Exception:
                    pass
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
        try:
            self.frames["alertas"].update_contents()
        except Exception:
            pass

    def apply_preferences(self, new_prefs: dict, save: bool = False):
        """
        Aplica inmediatamente las preferencias (formato, timezone, apariencia).
        Si save=True, también se guardan en disco y se persiste en self.prefs.
        """
        try:
            # aplicar preferencias al módulo centralizado (y opcionalmente persistir)
            preferences.apply(new_prefs, persist=save)
        except Exception:
            pass

        # cambiar apariencia si la pref lo incluye
        try:
            ap = new_prefs.get("appearance")
            if ap:
                # actualizar selector solo si existe (hemos removido el selector de la barra)
                if hasattr(self, "appearance"):
                    try:
                        self.appearance.set(ap)
                    except Exception:
                        pass
                self._change_appearance(ap)
        except Exception:
            pass

        # refrescar todos los frames para ver los cambios inmediatamente
        try:
            for f in self.frames.values():
                try:
                    f.update_contents()
                except Exception:
                    pass
        except Exception:
            pass

        # si se solicita, actualizar self.prefs y persistir
        if save:
            try:
                self.prefs.update(new_prefs)
                preferences.save(self.prefs)
            except Exception:
                pass

    def _open_settings(self):
        SettingsDialog(self, self.prefs, on_save=self._on_settings_saved)

    def _on_settings_saved(self, new_prefs):
        try:
            self.apply_preferences(new_prefs, save=True)
        except Exception:
            pass

# diálogo de configuración (igual funcionalmente que antes)
class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, prefs, on_save=None):
        super().__init__(parent)
        self.title("Configuración")
        self.geometry("480x380")
        self.parent = parent
        self.on_save = on_save
        self.prefs = prefs.copy()

        # transient pero SIN grab_set() para evitar bloqueos al cambiar apariencia
        try:
            self.transient(parent)
            self.lift()
            self.focus_force()
        except Exception:
            pass

        self.grid_columnconfigure((0,1), weight=1)

        ctk.CTkLabel(self, text="Símbolo de moneda:").grid(row=0, column=0, padx=12, pady=(12,4), sticky="w")
        self.var_currency = ctk.StringVar(value=self.prefs.get("currency_symbol", "$"))
        self.ent_currency = ctk.CTkEntry(self, textvariable=self.var_currency, placeholder_text="$")
        self.ent_currency.grid(row=0, column=1, padx=12, pady=(12,4), sticky="we")
        self.ent_currency.bind("<FocusOut>", lambda e: self._apply())

        ctk.CTkLabel(self, text="Posición del símbolo:").grid(row=1, column=0, padx=12, pady=4, sticky="w")
        self.opt_currency_pos = ctk.CTkOptionMenu(self, values=["before", "after"], command=lambda v: self._on_option_changed())
        self.opt_currency_pos.grid(row=1, column=1, padx=12, pady=4, sticky="we")
        try:
            self.opt_currency_pos.set(self.prefs.get("currency_position", "before"))
        except Exception:
            pass

        ctk.CTkLabel(self, text="Separador decimal:").grid(row=2, column=0, padx=12, pady=4, sticky="w")
        self.opt_decimal_sep = ctk.CTkOptionMenu(self, values=[".", ","], command=lambda v: self._on_option_changed())
        self.opt_decimal_sep.grid(row=2, column=1, padx=12, pady=4, sticky="we")
        try:
            self.opt_decimal_sep.set(self.prefs.get("decimal_separator", "."))
        except Exception:
            pass

        ctk.CTkLabel(self, text="Separador de miles:").grid(row=3, column=0, padx=12, pady=4, sticky="w")
        self.opt_thousands_sep = ctk.CTkOptionMenu(self, values=[",", ".", " "], command=lambda v: self._on_option_changed())
        self.opt_thousands_sep.grid(row=3, column=1, padx=12, pady=4, sticky="we")
        try:
            self.opt_thousands_sep.set(self.prefs.get("thousands_separator", ","))
        except Exception:
            pass

        ctk.CTkLabel(self, text="Decimales:").grid(row=4, column=0, padx=12, pady=4, sticky="w")
        self.var_decimals = ctk.StringVar(value=str(self.prefs.get("decimal_places", 2)))
        self.spin_decimals = ctk.CTkEntry(self, textvariable=self.var_decimals)
        self.spin_decimals.grid(row=4, column=1, padx=12, pady=4, sticky="we")
        self.spin_decimals.bind("<FocusOut>", lambda e: self._apply())

        ctk.CTkLabel(self, text="Zona horaria:").grid(row=5, column=0, padx=12, pady=4, sticky="w")
        tz_values = ["UTC", "Europe/Madrid", "America/Argentina/Buenos_Aires", "America/New_York", "America/Los_Angeles"]
        self.opt_timezone = ctk.CTkOptionMenu(self, values=tz_values, command=lambda v: self._on_option_changed())
        self.opt_timezone.grid(row=5, column=1, padx=12, pady=4, sticky="we")
        try:
            self.opt_timezone.set(self.prefs.get("timezone", "UTC"))
        except Exception:
            pass

        ctk.CTkLabel(self, text="Apariencia (tema):").grid(row=6, column=0, padx=12, pady=4, sticky="w")
        self.opt_appearance = ctk.CTkOptionMenu(self, values=["Light", "Dark", "System"], command=lambda v: self._on_option_changed())
        self.opt_appearance.grid(row=6, column=1, padx=12, pady=4, sticky="we")
        try:
            self.opt_appearance.set(self.prefs.get("appearance", "System"))
        except Exception:
            pass

        frm_btns = ctk.CTkFrame(self)
        frm_btns.grid(row=7, column=0, columnspan=2, pady=12, sticky="e", padx=12)
        btn_cancel = ctk.CTkButton(frm_btns, text="Cancelar", command=self.destroy)
        btn_cancel.grid(row=0, column=0, padx=(0,8))
        btn_apply = ctk.CTkButton(frm_btns, text="Aplicar", command=self._apply)
        btn_apply.grid(row=0, column=1, padx=(0,8))
        btn_ok = ctk.CTkButton(frm_btns, text="Guardar", command=self._on_ok)
        btn_ok.grid(row=0, column=2)

    def _on_option_changed(self):
        # aplicar con pequeño delay para evitar interrumpir el event loop
        try:
            self.after(50, self._apply)
        except Exception:
            try:
                self._apply()
            except Exception:
                pass

    def _gather_prefs(self) -> dict:
        try:
            dec_places = int(self.var_decimals.get())
            if dec_places < 0:
                dec_places = 2
        except Exception:
            dec_places = 2
        return {
            "currency_symbol": (self.var_currency.get() or "$"),
            "currency_position": self.opt_currency_pos.get(),
            "decimal_separator": self.opt_decimal_sep.get(),
            "thousands_separator": self.opt_thousands_sep.get(),
            "decimal_places": dec_places,
            "timezone": self.opt_timezone.get(),
            "appearance": self.opt_appearance.get()
        }

    def _apply(self):
        new = self._gather_prefs()
        try:
            # programar la aplicación en el padre usando after para evitar conflictos con ventanas modales
            if hasattr(self.parent, "apply_preferences"):
                try:
                    self.parent.after(50, lambda: self.parent.apply_preferences(new, save=False))
                except Exception:
                    self.parent.apply_preferences(new, save=False)
        except Exception:
            pass

    def _on_ok(self):
        new = self._gather_prefs()
        if callable(self.on_save):
            self.on_save(new)
        self.destroy()


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    db = os.path.join("data", "data.db")
    init_db(db)
    app = App(db)
    app.mainloop()
