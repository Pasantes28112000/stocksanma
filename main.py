# main.py
import os
import customtkinter as ctk
from lib_db import init_db, load_config, save_config
from login import LoginWindow
from funcs.dashboard_inventario import InventarioFrame
from funcs.dashboard_venta import VentaFrame
from funcs.dashboard_reposicion import ReposicionFrame
from funcs.dashboard_caja import CajaFrame
from funcs.dashboard_alertas import AlertasManager

APP_TITLE = "TecnoDashboard"

class Dashboard(ctk.CTk):
    def __init__(self, db, user, rol):
        super().__init__()
        self.db, self.user, self.rol = db, user, rol
        self.config_data = load_config()
        ctk.set_appearance_mode(self.config_data.get("modo", "Dark"))
        ctk.set_default_color_theme("dark-blue")
        self.title(f"{APP_TITLE} - {user} ({rol})")
        self.geometry("1200x700")
        self._build_ui()

    def _build_ui(self):
        top = ctk.CTkFrame(self, height=48)
        top.pack(fill="x", side="top")

        ctk.CTkLabel(top, text=APP_TITLE, font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=12)
        self.alert_icon = AlertasManager(top, self.db)
        self.alert_icon.pack(side="right", padx=8, pady=6)
        ctk.CTkButton(top, text="🔔 Limpiar", width=80, command=self.alert_icon.clear_alerts).pack(side="right", padx=6)
        ctk.CTkButton(top, text="⚙️", width=40, command=self._open_settings).pack(side="right", padx=8)

        main = ctk.CTkFrame(self)
        main.pack(fill="both", expand=True)

        self.sidebar = ctk.CTkFrame(main, width=200)
        self.sidebar.pack(side="left", fill="y", padx=8, pady=8)

        self.content = ctk.CTkFrame(main)
        self.content.pack(side="left", fill="both", expand=True, padx=8, pady=8)

        self.frames = {
            "inventario": InventarioFrame(self.content, self.db, self.config_data),
            "venta": VentaFrame(self.content, self.db, self.config_data),
            "reposicion": ReposicionFrame(self.content, self.db, self.config_data),
            "caja": CajaFrame(self.content, self.db, self.config_data)
        }

        items = [("Inventario", "inventario"), ("Venta", "venta"), ("Reposición", "reposicion"), ("Caja", "caja")]
        for text, key in items:
            if self.rol == "cajero" and key != "venta":
                continue
            ctk.CTkButton(self.sidebar, text=text, command=lambda k=key: self.show(k)).pack(pady=6, padx=8, fill="x")

        ctk.CTkButton(self.sidebar, text="Cerrar sesión", fg_color="gray30", command=self._logout).pack(side="bottom", pady=12, padx=8, fill="x")
        self.show("venta" if self.rol == "cajero" else "inventario")

    def show(self, key):
        for k, f in self.frames.items():
            f.pack_forget()
        for f in self.frames.values():
            f.config = self.config_data
        frame = self.frames[key]
        frame.pack(fill="both", expand=True)
        try:
            frame.update_contents()
        except Exception:
            if hasattr(frame, "_refresh_table"):
                frame._refresh_table()

    def _open_settings(self):
        SettingsWindow(self, dict(self.config_data), on_save=self._apply_config)

    def _apply_config(self, newconf):
        save_config(newconf)
        self.config_data = newconf
        ctk.set_appearance_mode(newconf.get("modo", "Dark"))
        # propagate config and refresh frames
        for f in self.frames.values():
            f.config = newconf
            try:
                f.update_contents()
            except Exception:
                if hasattr(f, "_refresh_table"):
                    f._refresh_table()
        # update alert icon
        try:
            self.alert_icon.check_alerts()
        except Exception:
            pass
        # apply font scaling across widgets
        self._apply_font_scale(newconf.get("fuente", 14))

    def _apply_font_scale(self, size):
        # Walk widget tree and update fonts where possible
        newfont = ctk.CTkFont(size=size)
        def recurse(w):
            for child in w.winfo_children():
                try:
                    # many CTk widgets accept 'font' configure
                    child.configure(font=newfont)
                except Exception:
                    pass
                recurse(child)
        recurse(self)

    def _logout(self):
        self.destroy()
        start_app()

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent, cfg, on_save):
        super().__init__(parent)
        self.parent = parent
        self.cfg = cfg
        self.on_save = on_save
        self.title("Configuración")
        self.geometry("420x360")
        self.transient(parent)
        self.attributes("-topmost", True)
        self.grab_set()
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Configuración", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=12)
        self.modo_var = ctk.StringVar(value=self.cfg.get("modo", "Dark"))
        ctk.CTkLabel(self, text="Apariencia").pack(anchor="w", padx=12)
        self.modo = ctk.CTkOptionMenu(self, values=["Dark", "Light"], variable=self.modo_var)
        self.modo.pack(padx=12, pady=6)

        ctk.CTkLabel(self, text="Símbolo monetario").pack(anchor="w", padx=12)
        self.moneda = ctk.CTkEntry(self)
        self.moneda.insert(0, self.cfg.get("moneda", "$"))
        self.moneda.pack(padx=12, pady=6)

        ctk.CTkLabel(self, text="Tamaño de fuente (escala)").pack(anchor="w", padx=12)
        self.fuente = ctk.CTkSlider(self, from_=10, to=22, number_of_steps=12)
        self.fuente.set(self.cfg.get("fuente", 14))
        self.fuente.pack(padx=12, pady=6)

        ctk.CTkLabel(self, text="IVA (%)").pack(anchor="w", padx=12)
        self.iva = ctk.CTkEntry(self)
        self.iva.insert(0, str(self.cfg.get("iva", 21)))
        self.iva.pack(padx=12, pady=6)

        ctk.CTkButton(self, text="Guardar y aplicar", command=self._save).pack(pady=16)

    def _save(self):
        try:
            newcfg = {
                "modo": self.modo.get(),
                "moneda": self.moneda.get() or "$",
                "fuente": int(self.fuente.get()),
                "iva": float(self.iva.get() or 21)
            }
        except Exception:
            newcfg = {"modo": "Dark", "moneda": "$", "fuente": 14, "iva": 21}
        self.on_save(newcfg)
        self.attributes("-topmost", False)
        self.destroy()

def start_app():
    os.makedirs("data", exist_ok=True)
    db = os.path.join("data", "data.db")
    init_db(db)

    def on_login(u, r):
        app = Dashboard(db, u, r)
        app.mainloop()

    login = LoginWindow(db, on_login)
    login.mainloop()

if __name__ == "__main__":
    start_app()
