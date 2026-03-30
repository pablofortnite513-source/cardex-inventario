import tkinter as tk
from tkinter import messagebox

from config.config import COLORS, USERS_FILE
from utils.data_handler import DataHandler


class CreateUserWindow:
    """Formulario para crear usuarios del sistema."""

    def __init__(self, parent: tk.Tk):
        self.window = tk.Toplevel(parent)
        self.window.title("Crear Usuario")
        self.window.geometry("920x360")
        self.window.configure(bg=COLORS["secondary"])

        self.fields: dict[str, tk.Entry] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        shell = tk.Frame(self.window, bg="white", bd=1, relief="solid", padx=14, pady=14)
        shell.pack(expand=True, fill="both", padx=14, pady=14)

        tk.Label(
            shell,
            text="Crear Usuario",
            bg=COLORS["primary"],
            fg=COLORS["text_light"],
            font=("Segoe UI", 20, "bold"),
            pady=6,
        ).pack(fill="x", pady=(0, 16))

        row1 = tk.Frame(shell, bg="white")
        row1.pack(fill="x", pady=(0, 14))
        self._add_field(row1, "Nombre Completo", "nombre", expand=True)

        row2 = tk.Frame(shell, bg="white")
        row2.pack(fill="x", pady=(0, 14))
        self._add_field(row2, "Usuario", "usuario")
        self._add_field(row2, "Contrasena", "contrasena", show="*")
        self._add_field(row2, "ROL", "rol")

        buttons = tk.Frame(shell, bg="white")
        buttons.pack(pady=(12, 0))

        tk.Button(
            buttons,
            text="Guardar",
            command=self.save,
            bg=COLORS["primary"],
            fg=COLORS["text_light"],
            relief="flat",
            font=("Segoe UI", 11, "bold"),
            padx=26,
            pady=8,
        ).pack(side="left", padx=14)

        tk.Button(
            buttons,
            text="Cancelar",
            command=self.window.destroy,
            bg=COLORS["primary"],
            fg=COLORS["text_light"],
            relief="flat",
            font=("Segoe UI", 11, "bold"),
            padx=26,
            pady=8,
        ).pack(side="left", padx=14)

    def _add_field(
        self,
        parent: tk.Widget,
        label_text: str,
        key: str,
        show: str | None = None,
        expand: bool = False,
    ) -> None:
        frame = tk.Frame(parent, bg="white")
        frame.pack(side="left", fill="x", expand=expand, padx=8)

        tk.Label(frame, text=label_text, bg="white", font=("Segoe UI", 11)).pack(anchor="w")
        entry = tk.Entry(frame, show=show if show else "")
        entry.pack(fill="x", pady=(4, 0))
        self.fields[key] = entry

    def save(self) -> None:
        nombre = self.fields["nombre"].get().strip()
        usuario = self.fields["usuario"].get().strip()
        contrasena = self.fields["contrasena"].get().strip()
        rol = self.fields["rol"].get().strip()

        if not all([nombre, usuario, contrasena, rol]):
            messagebox.showerror("Validacion", "Todos los campos son obligatorios")
            return

        usuarios = DataHandler.get_all(USERS_FILE, "usuarios")
        if any(u.get("usuario", "").lower() == usuario.lower() for u in usuarios):
            messagebox.showerror("Validacion", "Ese usuario ya existe")
            return

        record = {
            "nombre": nombre,
            "usuario": usuario,
            "contrasena": contrasena,
            "rol": rol,
        }

        if not DataHandler.add_record(USERS_FILE, "usuarios", record):
            messagebox.showerror("Error", "No se pudo guardar el usuario")
            return

        messagebox.showinfo("Exito", "Usuario creado correctamente")
        for entry in self.fields.values():
            entry.delete(0, tk.END)
