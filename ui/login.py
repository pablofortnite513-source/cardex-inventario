import tkinter as tk
from tkinter import messagebox

from config.config import COLORS, PROJECT_NAME, USERS_FILE
from ui.menu import MainMenuWindow
from utils.data_handler import DataHandler


class LoginWindow:
    """Pantalla de autenticacion de usuarios."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self._build_ui()

    def _build_ui(self) -> None:
        self.root.configure(bg=COLORS["secondary"])

        container = tk.Frame(self.root, bg=COLORS["secondary"], padx=20, pady=20)
        container.pack(expand=True, fill="both")

        card = tk.Frame(
            container,
            bg="white",
            bd=1,
            relief="solid",
            padx=25,
            pady=25,
        )
        card.pack(expand=True)

        tk.Label(
            card,
            text=PROJECT_NAME,
            font=("Segoe UI", 16, "bold"),
            bg="white",
            fg=COLORS["text_dark"],
        ).pack(pady=(0, 12))

        tk.Label(
            card,
            text="Inicio de sesion",
            font=("Segoe UI", 12),
            bg="white",
            fg=COLORS["text_dark"],
        ).pack(pady=(0, 20))

        tk.Label(card, text="Usuario", bg="white", anchor="w").pack(fill="x")
        self.user_entry = tk.Entry(card, width=30)
        self.user_entry.pack(pady=(0, 10))
        self.user_entry.bind("<Return>", lambda e: self.password_entry.focus_set())

        tk.Label(card, text="Contrasena", bg="white", anchor="w").pack(fill="x")
        self.password_entry = tk.Entry(card, width=30, show="*")
        self.password_entry.pack(pady=(0, 18))
        self.password_entry.bind("<Return>", lambda e: self.validate_login())

        button_row = tk.Frame(card, bg="white")
        button_row.pack(fill="x")

        tk.Button(
            button_row,
            text="Validar",
            bg=COLORS["primary"],
            fg=COLORS["text_light"],
            activebackground=COLORS["button_hover"],
            relief="flat",
            padx=10,
            pady=6,
            command=self.validate_login,
        ).pack(side="left", expand=True, fill="x", padx=(0, 8))

        tk.Button(
            button_row,
            text="Cerrar",
            bg=COLORS["border"],
            fg=COLORS["text_dark"],
            relief="flat",
            padx=10,
            pady=6,
            command=self.root.destroy,
        ).pack(side="left", expand=True, fill="x")

        self.user_entry.focus_set()
        """self.root.bind("<Return>", lambda _: self.validate_login())"""

    def validate_login(self) -> None:
        usuario = self.user_entry.get().strip()
        contrasena = self.password_entry.get().strip()

        if not usuario or not contrasena:
            messagebox.showerror("Error", "Completa usuario y contrasena")
            return
        
       
        data = DataHandler.load_json(USERS_FILE)
        usuarios = data.get("usuarios", [])

        user_found = next(
            (
                user
                for user in usuarios
                if user.get("usuario") == usuario and user.get("contrasena") == contrasena
            ),
            None,
        )

        if not user_found:
            messagebox.showerror("Acceso denegado", "Usuario o contrasena incorrectos")
            return

        for child in self.root.winfo_children():
            child.destroy()

        MainMenuWindow(self.root, user_found)
