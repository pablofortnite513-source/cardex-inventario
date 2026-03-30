import tkinter as tk
from tkinter import messagebox

from config.config import (
    ALMACENES_FILE,
    COLORS,
    PROVEEDORES_FILE,
    SUSTANCIAS_FILE,
    TIPOS_ENTRADA_FILE,
    UBICACIONES_FILE,
    UNIDADES_FILE,
)
from utils.data_handler import DataHandler


class MaestrasWindow:
    """Menu de maestras con acceso a catalogos base."""

    def __init__(self, parent: tk.Tk, auto_open: str | None = None):
        self.window = tk.Toplevel(parent)
        self.window.title("Maestras")
        self.window.geometry("760x420")
        self.window.configure(bg=COLORS["secondary"])
        self.auto_open = auto_open
        self._build_ui()

        if self.auto_open:
            self.open_from_label(self.auto_open)

    def _build_ui(self) -> None:
        wrapper = tk.Frame(self.window, bg="white", bd=1, relief="solid", padx=16, pady=16)
        wrapper.pack(expand=True, fill="both", padx=16, pady=16)

        tk.Label(
            wrapper,
            text="Maestras",
            bg="white",
            fg=COLORS["text_dark"],
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w", pady=(0, 12))

        grid = tk.Frame(wrapper, bg="white")
        grid.pack(expand=True, fill="both")

        options = [
            ("Sustancias", self.open_sustancias),
            ("T. Entrada", lambda: self.open_catalog("T. Entrada", TIPOS_ENTRADA_FILE, "tipos_entrada", "nombre")),
            ("Proveedor", lambda: self.open_catalog("Proveedor", PROVEEDORES_FILE, "proveedores", "nombre")),
            ("C. Almace", lambda: self.open_catalog("C. Almace", ALMACENES_FILE, "almacenes", "nombre")),
            ("Unidad", lambda: self.open_catalog("Unidad", UNIDADES_FILE, "unidades", "nombre")),
            ("Ubicacion", lambda: self.open_catalog("Ubicacion", UBICACIONES_FILE, "ubicaciones", "nombre")),
        ]

        for idx, (label, action) in enumerate(options):
            row = idx // 2
            col = idx % 2
            tk.Button(
                grid,
                text=label,
                bg="white",
                fg=COLORS["text_dark"],
                relief="solid",
                bd=1,
                font=("Segoe UI", 12),
                command=action,
                padx=20,
                pady=18,
            ).grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

        for row in range(3):
            grid.rowconfigure(row, weight=1)
        for col in range(2):
            grid.columnconfigure(col, weight=1)

    def open_catalog(self, title: str, file_path: str, key: str, display_field: str) -> None:
        MasterCatalogWindow(self.window, title, file_path, key, display_field)

    def open_sustancias(self) -> None:
        SubstanceMasterWindow(self.window)

    def open_from_label(self, label: str) -> None:
        mapping = {
            "Sustancias": self.open_sustancias,
            "T. Entrada": lambda: self.open_catalog("T. Entrada", TIPOS_ENTRADA_FILE, "tipos_entrada", "nombre"),
            "Proveedor": lambda: self.open_catalog("Proveedor", PROVEEDORES_FILE, "proveedores", "nombre"),
            "C. Almace": lambda: self.open_catalog("C. Almace", ALMACENES_FILE, "almacenes", "nombre"),
            "Unidad": lambda: self.open_catalog("Unidad", UNIDADES_FILE, "unidades", "nombre"),
            "Ubicacion": lambda: self.open_catalog("Ubicacion", UBICACIONES_FILE, "ubicaciones", "nombre"),
        }
        action = mapping.get(label)
        if action:
            action()


class SubstanceMasterWindow:
    """Formulario visual de maestra de sustancias, alineado con el formato del sistema origen."""

    def __init__(self, parent: tk.Toplevel):
        self.window = tk.Toplevel(parent)
        self.window.title("Maestra de Sustancia")
        self.window.geometry("980x480")
        self.window.configure(bg=COLORS["secondary"])

        self.control_var = tk.StringVar(value="No")
        self.inputs: dict[str, tk.Entry] = {}

        self._build_ui()

    def _build_ui(self) -> None:
        shell = tk.Frame(self.window, bg="white", bd=1, relief="solid", padx=14, pady=14)
        shell.pack(expand=True, fill="both", padx=12, pady=12)

        header = tk.Label(
            shell,
            text="Maestra de Sustancia",
            bg=COLORS["primary"],
            fg=COLORS["text_light"],
            font=("Segoe UI", 22, "bold"),
            pady=8,
        )
        header.pack(fill="x", pady=(0, 16))

        grid = tk.Frame(shell, bg="white")
        grid.pack(fill="both", expand=True)

        self._add_field(grid, "Codigo", 0, 0)
        self._add_field(grid, "Nombre del Producto", 0, 1)
        self._add_field(grid, "Codigo CAS", 0, 2)

        control_box = tk.LabelFrame(
            grid,
            text="Sustancia Controlada",
            bg="white",
            fg=COLORS["text_dark"],
            font=("Segoe UI", 11),
        )
        control_box.grid(row=2, column=0, sticky="ew", padx=8, pady=8)
        tk.Radiobutton(
            control_box,
            text="SI",
            variable=self.control_var,
            value="Si",
            bg="white",
            font=("Segoe UI", 11, "bold"),
        ).pack(side="left", padx=16, pady=8)
        tk.Radiobutton(
            control_box,
            text="NO",
            variable=self.control_var,
            value="No",
            bg="white",
            font=("Segoe UI", 11, "bold"),
        ).pack(side="left", padx=16, pady=8)

        self._add_field(grid, "Limite Minimo de Control", 1, 1)
        self._add_field(grid, "Codigo Sistema", 1, 2)
        self._add_field(grid, "Cantidad Minima Stock", 2, 2)

        for col in range(3):
            grid.columnconfigure(col, weight=1)

        buttons = tk.Frame(shell, bg="white")
        buttons.pack(fill="x", pady=(10, 0))

        tk.Button(
            buttons,
            text="Guardar",
            command=self.save,
            bg=COLORS["primary"],
            fg=COLORS["text_light"],
            relief="flat",
            font=("Segoe UI", 11, "bold"),
            padx=24,
            pady=8,
        ).pack(side="right", padx=(10, 0))

        tk.Button(
            buttons,
            text="Salir",
            command=self.window.destroy,
            bg=COLORS["primary"],
            fg=COLORS["text_light"],
            relief="flat",
            font=("Segoe UI", 11, "bold"),
            padx=24,
            pady=8,
        ).pack(side="right")

    def _add_field(self, parent: tk.Widget, label: str, row: int, col: int) -> None:
        frame = tk.Frame(parent, bg="white")
        frame.grid(row=row * 2, column=col, sticky="ew", padx=8, pady=(4, 0))

        tk.Label(
            frame,
            text=label,
            bg="white",
            fg=COLORS["text_dark"],
            font=("Segoe UI", 11),
        ).pack(anchor="w")

        entry = tk.Entry(frame, font=("Segoe UI", 11))
        entry.pack(fill="x", pady=(3, 4))
        self.inputs[label] = entry

    def save(self) -> None:
        codigo = self.inputs["Codigo"].get().strip()
        nombre = self.inputs["Nombre del Producto"].get().strip()

        if not codigo or not nombre:
            messagebox.showerror("Validacion", "Codigo y Nombre del Producto son obligatorios")
            return

        data = DataHandler.load_json(SUSTANCIAS_FILE)
        sustancias = data.get("sustancias", [])

        if any(item.get("codigo") == codigo for item in sustancias):
            messagebox.showerror("Validacion", "Ya existe una sustancia con ese codigo")
            return

        record = {
            "codigo": codigo,
            "nombre": nombre,
            "codigo_cas": self.inputs["Codigo CAS"].get().strip(),
            "controlada": self.control_var.get(),
            "limite_minimo_control": self.inputs["Limite Minimo de Control"].get().strip(),
            "codigo_sistema": self.inputs["Codigo Sistema"].get().strip(),
            "cantidad_minima_stock": self.inputs["Cantidad Minima Stock"].get().strip(),
            "concentracion": "",
            "densidad": "",
            "unidad": "",
        }

        if not DataHandler.add_record(SUSTANCIAS_FILE, "sustancias", record):
            messagebox.showerror("Error", "No se pudo guardar la sustancia")
            return

        messagebox.showinfo("Exito", "Sustancia guardada correctamente")
        for input_entry in self.inputs.values():
            input_entry.delete(0, tk.END)
        self.control_var.set("No")


class MasterCatalogWindow:
    """Catalogo sencillo para agregar items a una maestra."""

    def __init__(self, parent: tk.Toplevel, title: str, file_path: str, key: str, display_field: str):
        self.file_path = file_path
        self.key = key
        self.display_field = display_field

        self.window = tk.Toplevel(parent)
        self.window.title(f"Maestra - {title}")
        self.window.geometry("500x420")
        self.window.configure(bg=COLORS["secondary"])

        self._build_ui(title)
        self.reload_items()

    def _build_ui(self, title: str) -> None:
        card = tk.Frame(self.window, bg="white", bd=1, relief="solid", padx=14, pady=14)
        card.pack(expand=True, fill="both", padx=14, pady=14)

        tk.Label(
            card,
            text=f"Catalogo: {title}",
            bg="white",
            fg=COLORS["text_dark"],
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w", pady=(0, 10))

        self.listbox = tk.Listbox(card, height=12)
        self.listbox.pack(fill="both", expand=True)

        entry_row = tk.Frame(card, bg="white")
        entry_row.pack(fill="x", pady=(10, 0))

        self.name_entry = tk.Entry(entry_row)
        self.name_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        tk.Button(
            entry_row,
            text="Agregar",
            bg=COLORS["primary"],
            fg=COLORS["text_light"],
            relief="flat",
            command=self.add_item,
        ).pack(side="left")

        action_row = tk.Frame(card, bg="white")
        action_row.pack(fill="x", pady=(10, 0))

        tk.Button(
            action_row,
            text="Eliminar seleccionado",
            bg=COLORS["error"],
            fg=COLORS["text_light"],
            relief="flat",
            command=self.delete_selected,
        ).pack(side="left")

        tk.Button(
            action_row,
            text="Actualizar",
            bg=COLORS["border"],
            fg=COLORS["text_dark"],
            relief="flat",
            command=self.reload_items,
        ).pack(side="right")

    def reload_items(self) -> None:
        data = DataHandler.load_json(self.file_path)
        records = data.get(self.key, [])

        self.listbox.delete(0, tk.END)
        for record in records:
            value = record.get(self.display_field, "")
            if value:
                self.listbox.insert(tk.END, value)

    def add_item(self) -> None:
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Validacion", "Ingresa un valor para agregar")
            return

        payload = {self.display_field: name}

        if self.key == "unidades":
            payload = {"codigo": name.lower(), "nombre": name}
        elif self.key == "ubicaciones":
            payload = {"codigo": f"UB{str(self.listbox.size() + 1).zfill(3)}", "nombre": name, "almacen": ""}

        saved = DataHandler.add_record(self.file_path, self.key, payload)
        if not saved:
            messagebox.showerror("Error", "No se pudo guardar el registro")
            return

        self.name_entry.delete(0, tk.END)
        self.reload_items()

    def delete_selected(self) -> None:
        selected = self.listbox.curselection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecciona un item para eliminar")
            return

        selected_name = self.listbox.get(selected[0])
        data = DataHandler.load_json(self.file_path)
        records = data.get(self.key, [])

        filtered = [r for r in records if r.get(self.display_field, "") != selected_name]
        data[self.key] = filtered

        if not DataHandler.save_json(self.file_path, data):
            messagebox.showerror("Error", "No se pudo eliminar el registro")
            return

        self.reload_items()
