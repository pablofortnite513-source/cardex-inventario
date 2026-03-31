import tkinter as tk
from tkinter import messagebox, ttk

from config.config import COLORS, USERS_FILE
from utils.data_handler import DataHandler

PERMISSION_MODULES = [
    ("Inventario", "inventario"),
    ("Entradas", "entradas"),
    ("Salidas", "salidas"),
    ("Stock", "stock"),
    ("Consulta", "consulta"),
    ("Vigencias", "vigencias"),
    ("Auditoria", "auditoria"),
]


class CreateUserWindow:
    """Formulario para crear usuarios del sistema con permisos granulares."""

    def __init__(self, parent: tk.Tk):
        self.window = tk.Toplevel(parent)
        self.window.title("Gestión de Usuarios")
        self.window.geometry("1060x520")
        self.window.configure(bg=COLORS["secondary"])

        self.fields: dict[str, tk.Entry] = {}
        self.perm_vars: dict[str, tk.BooleanVar] = {}
        self.tree: ttk.Treeview | None = None
        self._build_ui()
        self._load_table()

    def _build_ui(self) -> None:
        shell = tk.Frame(self.window, bg="white", bd=1, relief="solid", padx=14, pady=14)
        shell.pack(expand=True, fill="both", padx=14, pady=14)

        tk.Label(
            shell,
            text="Gestión de Usuarios",
            bg=COLORS["primary"],
            fg=COLORS["text_light"],
            font=("Segoe UI", 18, "bold"),
            pady=6,
        ).pack(fill="x", pady=(0, 12))

        form = tk.Frame(shell, bg="white")
        form.pack(fill="x", pady=(0, 10))

        row1 = tk.Frame(form, bg="white")
        row1.pack(fill="x", pady=(0, 8))
        self._add_field(row1, "Nombre Completo", "nombre", expand=True)

        row2 = tk.Frame(form, bg="white")
        row2.pack(fill="x", pady=(0, 8))
        self._add_field(row2, "Usuario", "usuario")
        self._add_field(row2, "Contraseña", "contrasena", show="*")
        self._add_field(row2, "Permiso (Admin/Reporte)", "rol")

        perm_frame = tk.LabelFrame(form, text="Permisos por Módulo", bg="white", fg="#1F4F8A", font=("Segoe UI", 10, "bold"))
        perm_frame.pack(fill="x", pady=(0, 8), padx=4)
        perm_row = tk.Frame(perm_frame, bg="white")
        perm_row.pack(fill="x", padx=10, pady=8)
        for idx, (label, key) in enumerate(PERMISSION_MODULES):
            var = tk.BooleanVar(value=False)
            self.perm_vars[key] = var
            tk.Checkbutton(perm_row, text=label, variable=var, bg="white", font=("Segoe UI", 10)).grid(row=0, column=idx, padx=10, sticky="w")

        buttons = tk.Frame(form, bg="white")
        buttons.pack(fill="x", pady=(4, 8))
        tk.Button(buttons, text="Guardar", command=self.save, bg=COLORS["primary"], fg=COLORS["text_light"], relief="flat", padx=20, pady=6).pack(side="left", padx=4)
        tk.Button(buttons, text="Limpiar", command=self._clear, bg=COLORS["border"], fg=COLORS["text_dark"], relief="flat", padx=20, pady=6).pack(side="left", padx=4)
        tk.Button(buttons, text="Salir", command=self.window.destroy, bg=COLORS["primary"], fg=COLORS["text_light"], relief="flat", padx=20, pady=6).pack(side="right", padx=4)

        cols = ("nombre", "usuario", "rol", "entradas", "salidas", "stock", "consulta", "vigencias", "auditoria")
        self.tree = ttk.Treeview(shell, columns=cols, show="headings", height=8)
        self.tree.pack(expand=True, fill="both")
        for c in cols:
            self.tree.heading(c, text=c.capitalize())
            self.tree.column(c, width=100, anchor="w")

    def _add_field(self, parent: tk.Widget, label_text: str, key: str, show: str | None = None, expand: bool = False) -> None:
        frame = tk.Frame(parent, bg="white")
        frame.pack(side="left", fill="x", expand=expand, padx=8)
        tk.Label(frame, text=label_text, bg="white", font=("Segoe UI", 10)).pack(anchor="w")
        entry = tk.Entry(frame, show=show if show else "")
        entry.pack(fill="x", pady=(4, 0))
        self.fields[key] = entry

    def _load_table(self) -> None:
        if self.tree is None:
            return
        self.tree.delete(*self.tree.get_children())
        usuarios = DataHandler.get_all(USERS_FILE, "usuarios")
        for u in usuarios:
            perms = u.get("permisos", {})
            self.tree.insert("", tk.END, values=(
                u.get("nombre", ""),
                u.get("usuario", ""),
                u.get("rol", ""),
                "SI" if perms.get("entradas") else "NO",
                "SI" if perms.get("salidas") else "NO",
                "SI" if perms.get("stock") else "NO",
                "SI" if perms.get("consulta") else "NO",
                "SI" if perms.get("vigencias") else "NO",
                "SI" if perms.get("auditoria") else "NO",
            ))

    def _clear(self) -> None:
        for entry in self.fields.values():
            entry.delete(0, tk.END)
        for var in self.perm_vars.values():
            var.set(False)

    def save(self) -> None:
        nombre = self.fields["nombre"].get().strip()
        usuario = self.fields["usuario"].get().strip()
        contrasena = self.fields["contrasena"].get().strip()
        rol = self.fields["rol"].get().strip()

        if not all([nombre, usuario, contrasena, rol]):
            messagebox.showerror("Validación", "Nombre, Usuario, Contraseña y Permiso son obligatorios")
            return

        usuarios = DataHandler.get_all(USERS_FILE, "usuarios")
        if any(u.get("usuario", "").lower() == usuario.lower() for u in usuarios):
            messagebox.showerror("Validación", "Ese usuario ya existe")
            return

        permisos = {key: var.get() for key, var in self.perm_vars.items()}

        record = {
            "nombre": nombre,
            "usuario": usuario,
            "contrasena": contrasena,
            "rol": rol,
            "permisos": permisos,
        }

        if not DataHandler.add_record(USERS_FILE, "usuarios", record):
            messagebox.showerror("Error", "No se pudo guardar el usuario")
            return

        messagebox.showinfo("Éxito", "Usuario creado correctamente")
        self._clear()
        self._load_table()
