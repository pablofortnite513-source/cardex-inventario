import tkinter as tk
from pathlib import Path
from tkinter import filedialog
from tkinter import messagebox, ttk
import shutil

from config.config import COLORS, FIRMAS_PATH, USERS_FILE
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
        self.role_var = tk.StringVar(value="Operario")
        self.tree: ttk.Treeview | None = None
        self.selected_user_id: int | None = None
        self.signature_path_var = tk.StringVar()
        self.signature_password_var = tk.StringVar()
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

        role_frame = tk.Frame(row2, bg="white")
        role_frame.pack(side="left", fill="x", expand=False, padx=8)
        tk.Label(role_frame, text="Rol", bg="white", font=("Segoe UI", 10)).pack(anchor="w")
        role_combo = ttk.Combobox(
            role_frame,
            textvariable=self.role_var,
            values=["Admin", "Operario", "Consulta"],
            state="readonly",
            width=18,
        )
        role_combo.pack(fill="x", pady=(4, 0))
        role_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_role_change())

        perm_frame = tk.LabelFrame(form, text="Permisos por Módulo", bg="white", fg="#1F4F8A", font=("Segoe UI", 10, "bold"))
        perm_frame.pack(fill="x", pady=(0, 8), padx=4)
        perm_row = tk.Frame(perm_frame, bg="white")
        perm_row.pack(fill="x", padx=10, pady=8)
        for idx, (label, key) in enumerate(PERMISSION_MODULES):
            var = tk.BooleanVar(value=False)
            self.perm_vars[key] = var
            tk.Checkbutton(perm_row, text=label, variable=var, bg="white", font=("Segoe UI", 10)).grid(row=0, column=idx, padx=10, sticky="w")
        tk.Button(
            perm_row,
            text="Agregar firma",
            command=self._open_signature_window,
            bg="white",
            fg="#1F4F8A",
            relief="solid",
            padx=10,
            pady=2,
        ).grid(row=0, column=len(PERMISSION_MODULES), padx=(14, 0), sticky="w")

        buttons = tk.Frame(form, bg="white")
        buttons.pack(fill="x", pady=(4, 8))
        tk.Button(buttons, text="Guardar", command=self.save, bg=COLORS["primary"], fg=COLORS["text_light"], relief="flat", padx=20, pady=6).pack(side="left", padx=4)
        tk.Button(buttons, text="Modificar", command=self.update_selected, bg=COLORS["primary"], fg=COLORS["text_light"], relief="flat", padx=20, pady=6).pack(side="left", padx=4)
        tk.Button(buttons, text="Eliminar", command=self.delete_selected, bg=COLORS["error"], fg=COLORS["text_light"], relief="flat", padx=20, pady=6).pack(side="left", padx=4)
        tk.Button(buttons, text="Limpiar", command=self._clear, bg=COLORS["border"], fg=COLORS["text_dark"], relief="flat", padx=20, pady=6).pack(side="left", padx=4)
        tk.Button(buttons, text="Salir", command=self.window.destroy, bg=COLORS["primary"], fg=COLORS["text_light"], relief="flat", padx=20, pady=6).pack(side="right", padx=4)

        cols = ("id", "nombre", "usuario", "rol", "entradas", "salidas", "stock", "consulta", "vigencias", "auditoria", "firma")
        self.tree = ttk.Treeview(shell, columns=cols, show="headings", height=8)
        self.tree.pack(expand=True, fill="both")
        for c in cols:
            self.tree.heading(c, text=c.capitalize())
            if c == "id":
                self.tree.column(c, width=0, minwidth=0, stretch=False)
            else:
                self.tree.column(c, width=100, anchor="w")
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

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
                u.get("id", ""),
                u.get("nombre", ""),
                u.get("usuario", ""),
                u.get("rol", ""),
                "SI" if perms.get("entradas") else "NO",
                "SI" if perms.get("salidas") else "NO",
                "SI" if perms.get("stock") else "NO",
                "SI" if perms.get("consulta") else "NO",
                "SI" if perms.get("vigencias") else "NO",
                "SI" if perms.get("auditoria") else "NO",
                "SI" if str(u.get("firma_path", "")).strip() else "NO",
            ))

    def _on_tree_select(self, _event=None) -> None:
        if self.tree is None:
            return
        selected = self.tree.selection()
        if not selected:
            return

        values = self.tree.item(selected[0], "values")
        if not values:
            return

        try:
            selected_id = int(values[0])
        except (TypeError, ValueError):
            return

        usuarios = DataHandler.get_all(USERS_FILE, "usuarios")
        target = next((u for u in usuarios if u.get("id") == selected_id), None)
        if target is None:
            return

        self.selected_user_id = selected_id
        self.fields["nombre"].delete(0, tk.END)
        self.fields["nombre"].insert(0, str(target.get("nombre", "")))
        self.fields["usuario"].delete(0, tk.END)
        self.fields["usuario"].insert(0, str(target.get("usuario", "")))
        self.fields["contrasena"].delete(0, tk.END)
        self.fields["contrasena"].insert(0, str(target.get("contrasena", "")))
        self.role_var.set(str(target.get("rol", "Operario")) or "Operario")
        self.signature_path_var.set(str(target.get("firma_path", "")))
        self.signature_password_var.set(str(target.get("firma_password", "")))

        perms = target.get("permisos", {})
        for key, var in self.perm_vars.items():
            var.set(bool(perms.get(key, False)))

    def _clear(self) -> None:
        for entry in self.fields.values():
            entry.delete(0, tk.END)
        self.selected_user_id = None
        self.role_var.set("Operario")
        self.signature_path_var.set("")
        self.signature_password_var.set("")
        for var in self.perm_vars.values():
            var.set(False)
        self._on_role_change()

    def _open_signature_window(self) -> None:
        if self.selected_user_id is None:
            messagebox.showwarning("Aviso", "Selecciona un usuario para agregar o actualizar su firma")
            return

        top = tk.Toplevel(self.window)
        top.title("Agregar Firma")
        top.geometry("520x220")
        top.configure(bg="white")
        top.transient(self.window)
        top.grab_set()

        path_var = tk.StringVar(value=self.signature_path_var.get())
        pass_var = tk.StringVar(value=self.signature_password_var.get())

        frm = tk.Frame(top, bg="white", padx=14, pady=14)
        frm.pack(fill="both", expand=True)

        tk.Label(frm, text="Archivo de firma", bg="white").grid(row=0, column=0, sticky="w")
        tk.Entry(frm, textvariable=path_var, state="readonly").grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(4, 10))
        tk.Button(
            frm,
            text="Buscar",
            command=lambda: self._pick_signature_file(path_var),
            bg=COLORS["border"],
            fg=COLORS["text_dark"],
            relief="flat",
            padx=12,
            pady=5,
        ).grid(row=1, column=1, sticky="ew", pady=(4, 10))

        tk.Label(frm, text="Contraseña firma", bg="white").grid(row=2, column=0, sticky="w")
        tk.Entry(frm, textvariable=pass_var, show="*").grid(row=3, column=0, columnspan=2, sticky="ew", pady=(4, 12))

        btns = tk.Frame(frm, bg="white")
        btns.grid(row=4, column=0, columnspan=2, sticky="e")
        tk.Button(
            btns,
            text="Guardar firma",
            command=lambda: self._save_signature_for_selected(path_var, pass_var, top),
            bg=COLORS["primary"],
            fg=COLORS["text_light"],
            relief="flat",
            padx=12,
            pady=5,
        ).pack(side="left", padx=(0, 8))
        tk.Button(
            btns,
            text="Cancelar",
            command=top.destroy,
            bg=COLORS["border"],
            fg=COLORS["text_dark"],
            relief="flat",
            padx=12,
            pady=5,
        ).pack(side="left")

        frm.columnconfigure(0, weight=1)

    def _pick_signature_file(self, target_var: tk.StringVar) -> None:
        selected = filedialog.askopenfilename(
            parent=self.window,
            title="Seleccionar firma",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.gif *.bmp *.webp")],
        )
        if selected:
            target_var.set(selected)

    def _save_signature_for_selected(self, path_var: tk.StringVar, pass_var: tk.StringVar, top: tk.Toplevel) -> None:
        if self.selected_user_id is None:
            messagebox.showwarning("Aviso", "Selecciona un usuario", parent=top)
            return

        src = path_var.get().strip()
        password = pass_var.get().strip()
        if not src:
            messagebox.showerror("Validación", "Selecciona un archivo de firma", parent=top)
            return
        if not password:
            messagebox.showerror("Validación", "La contraseña de firma es obligatoria", parent=top)
            return
        if not Path(src).exists():
            messagebox.showerror("Validación", "El archivo de firma no existe", parent=top)
            return

        usuarios = DataHandler.get_all(USERS_FILE, "usuarios")
        target = next((u for u in usuarios if u.get("id") == self.selected_user_id), None)
        if target is None:
            messagebox.showerror("Error", "Usuario no encontrado", parent=top)
            return

        FIRMAS_PATH.mkdir(parents=True, exist_ok=True)
        ext = Path(src).suffix.lower() or ".png"
        safe_user = str(target.get("usuario", "usuario")).strip().replace(" ", "_")
        dest = FIRMAS_PATH / f"firma_{safe_user}_{self.selected_user_id}{ext}"

        try:
            shutil.copy2(src, dest)
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo copiar la firma: {exc}", parent=top)
            return

        updates = {
            "nombre": target.get("nombre", ""),
            "usuario": target.get("usuario", ""),
            "contrasena": target.get("contrasena", ""),
            "rol": target.get("rol", ""),
            "permisos": target.get("permisos", {}),
            "firma_path": str(dest),
            "firma_password": password,
        }
        if not DataHandler.update_record(USERS_FILE, "usuarios", self.selected_user_id, updates):
            messagebox.showerror("Error", "No se pudo guardar la firma", parent=top)
            return

        self.signature_path_var.set(str(dest))
        self.signature_password_var.set(password)
        self._load_table()
        messagebox.showinfo("Éxito", "Firma guardada correctamente", parent=top)
        top.destroy()

    def update_selected(self) -> None:
        if self.selected_user_id is None:
            messagebox.showwarning("Aviso", "Selecciona un usuario para modificar")
            return

        nombre = self.fields["nombre"].get().strip()
        usuario = self.fields["usuario"].get().strip()
        contrasena = self.fields["contrasena"].get().strip()
        rol = self.role_var.get().strip()

        if not all([nombre, usuario, contrasena, rol]):
            messagebox.showerror("Validación", "Nombre, Usuario, Contraseña y Rol son obligatorios")
            return

        usuarios = DataHandler.get_all(USERS_FILE, "usuarios")
        if any(
            u.get("id") != self.selected_user_id and u.get("usuario", "").lower() == usuario.lower()
            for u in usuarios
        ):
            messagebox.showerror("Validación", "Ese usuario ya existe")
            return

        permisos = {key: var.get() for key, var in self.perm_vars.items()}
        if rol.lower() == "admin":
            permisos = {key: True for _label, key in PERMISSION_MODULES}

        updates = {
            "nombre": nombre,
            "usuario": usuario,
            "contrasena": contrasena,
            "rol": rol,
            "permisos": permisos,
            "firma_path": self.signature_path_var.get().strip(),
            "firma_password": self.signature_password_var.get().strip(),
        }

        if not DataHandler.update_record(USERS_FILE, "usuarios", self.selected_user_id, updates):
            messagebox.showerror("Error", "No se pudo modificar el usuario")
            return

        messagebox.showinfo("Éxito", "Usuario modificado correctamente")
        self._clear()
        self._load_table()

    def delete_selected(self) -> None:
        if self.selected_user_id is None:
            messagebox.showwarning("Aviso", "Selecciona un usuario para eliminar")
            return

        usuarios_data = DataHandler.load_json(USERS_FILE)
        usuarios = usuarios_data.get("usuarios", [])
        target = next((u for u in usuarios if u.get("id") == self.selected_user_id), None)
        if target is None:
            messagebox.showerror("Error", "Usuario no encontrado")
            return

        if not messagebox.askyesno("Confirmar", f"¿Desea eliminar el usuario '{target.get('usuario', '')}'?"):
            return

        usuarios_data["usuarios"] = [u for u in usuarios if u.get("id") != self.selected_user_id]
        if not DataHandler.save_json(USERS_FILE, usuarios_data):
            messagebox.showerror("Error", "No se pudo eliminar el usuario")
            return

        messagebox.showinfo("Éxito", "Usuario eliminado correctamente")
        self._clear()
        self._load_table()

    def _on_role_change(self) -> None:
        role = self.role_var.get().strip().lower()
        if role == "admin":
            for var in self.perm_vars.values():
                var.set(True)

    def save(self) -> None:
        original_cursor = self.window.cget("cursor")
        self.window.config(cursor="watch")
        self.window.update()
        nombre = self.fields["nombre"].get().strip()
        usuario = self.fields["usuario"].get().strip()
        contrasena = self.fields["contrasena"].get().strip()
        rol = self.role_var.get().strip()

        if not all([nombre, usuario, contrasena, rol]):
            messagebox.showerror("Validación", "Nombre, Usuario, Contraseña y Permiso son obligatorios")
            self.window.config(cursor=original_cursor)
            return

        usuarios = DataHandler.get_all(USERS_FILE, "usuarios")
        if any(u.get("usuario", "").lower() == usuario.lower() for u in usuarios):
            messagebox.showerror("Validación", "Ese usuario ya existe")
            self.window.config(cursor=original_cursor)
            return

        permisos = {key: var.get() for key, var in self.perm_vars.items()}
        if rol.lower() == "admin":
            permisos = {key: True for _label, key in PERMISSION_MODULES}

        record = {
            "nombre": nombre,
            "usuario": usuario,
            "contrasena": contrasena,
            "rol": rol,
            "permisos": permisos,
            "firma_path": self.signature_path_var.get().strip(),
            "firma_password": self.signature_password_var.get().strip(),
        }

        if not DataHandler.add_record(USERS_FILE, "usuarios", record):
            messagebox.showerror("Error", "No se pudo guardar el usuario")
            self.window.config(cursor=original_cursor)
            return

        messagebox.showinfo("Éxito", "Usuario creado correctamente")
        self._clear()
        self._load_table()
        self.window.config(cursor=original_cursor)
