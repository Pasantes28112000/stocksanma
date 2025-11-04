import customtkinter as ctk
import tkinter.messagebox as mb
from lib_db import validate_login, register_user

class LoginWindow(ctk.CTk):
    def __init__(self, db_path, callback):
        super().__init__()
        self.db_path = db_path
        self.callback = callback
        self.geometry("400x360")
        self.title("TecnoDashboard - Acceso")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("dark-blue")
        self._build_login()

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()

    def _build_login(self):
        self._clear()
        ctk.CTkLabel(self, text="Iniciar sesión", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=20)
        self.user_entry = ctk.CTkEntry(self, placeholder_text="Usuario")
        self.user_entry.pack(pady=8)
        self.pass_entry = ctk.CTkEntry(self, placeholder_text="Contraseña", show="*")
        self.pass_entry.pack(pady=8)

        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=8)
        ctk.CTkButton(btn_frame, text="Ingresar", command=self._login).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="Crear cuenta", fg_color="gray30", command=self._build_register).pack(side="left", padx=8)

        # TAB y ENTER
        self.user_entry.bind("<Tab>", lambda e: (self.pass_entry.focus_set(), "break"))
        self.user_entry.bind("<Return>", lambda e: (self.pass_entry.focus_set(), "break"))
        self.pass_entry.bind("<Return>", lambda e: (self._login(), "break"))

        self.user_entry.focus_set()

    def _build_register(self):
        self._clear()
        ctk.CTkLabel(self, text="Registrar nuevo usuario", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=20)
        self.new_user = ctk.CTkEntry(self, placeholder_text="Usuario")
        self.new_user.pack(pady=8)
        self.new_pass = ctk.CTkEntry(self, placeholder_text="Contraseña", show="*")
        self.new_pass.pack(pady=8)
        self.rol = ctk.CTkOptionMenu(self, values=["admin", "cajero"])
        self.rol.pack(pady=8)
        ctk.CTkButton(self, text="Registrar", command=self._do_register).pack(pady=10)
        ctk.CTkButton(self, text="Volver", fg_color="gray30", command=self._build_login).pack(pady=4)

    def _login(self):
        u, p = self.user_entry.get(), self.pass_entry.get()
        if not u or not p:
            mb.showwarning("Campos vacíos", "Ingrese usuario y contraseña")
            return
        rol = validate_login(self.db_path, u, p)
        if rol:
            self.withdraw()
            self.callback(u, rol)
            self.after(150, self.destroy)
        else:
            mb.showerror("Error", "Credenciales incorrectas")

    def _do_register(self):
        u, p, r = self.new_user.get(), self.new_pass.get(), self.rol.get()
        if not u or not p:
            mb.showwarning("Campos vacíos", "Complete todos los campos")
            return
        if register_user(self.db_path, u, p, r):
            mb.showinfo("Éxito", f"Usuario '{u}' creado correctamente")
            self._build_login()
        else:
            mb.showerror("Error", "El usuario ya existe")
