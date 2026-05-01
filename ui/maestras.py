import tkinter as tk
from tkinter import messagebox, ttk

from config.config import (
    ALMACENES_FILE,
    COLORS,
    CONDICIONES_FILE,
    INVENTARIO_FILE,
    PROVEEDORES_FILE,
    SUSTANCIAS_FILE,
    TIPOS_ENTRADA_FILE,
    TIPOS_SALIDA_FILE,
    UBICACIONES_FILE,
    UBICACIONES_USO_FILE,
    UNIDADES_FILE,
)
from ui.bitacora import registrar_bitacora
from utils.data_handler import DataHandler, Lookups, build_location_indexes, location_name


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
            ("T. Entrada", lambda: self.open_catalog("T. Entrada", TIPOS_ENTRADA_FILE, "maestrasTiposEntrada", "nombre")),
            ("T. Salida", lambda: self.open_catalog("T. Salida", TIPOS_SALIDA_FILE, "maestrasTiposSalida", "nombre")),
            ("Proveedor", lambda: self.open_catalog("Proveedor", PROVEEDORES_FILE, "maestrasProveedores", "nombre")),
            ("C. Almace", lambda: self.open_catalog("C. Almace", ALMACENES_FILE, "maestrasAlmacenes", "nombre")),
            ("Unidad", lambda: self.open_catalog("Unidad", UNIDADES_FILE, "maestrasUnidades", "nombre")),
            ("Ubicacion", self.open_ubicacion),
            ("Cond. Almac.", lambda: self.open_catalog("Cond. Almac.", CONDICIONES_FILE, "maestrasCondicionesAlmacenamiento", "nombre")),
        ]

        for idx, (label, action) in enumerate(options):
            row = idx // 3
            col = idx % 3
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
        for col in range(3):
            grid.columnconfigure(col, weight=1)

    def open_catalog(self, title: str, file_path: str, key: str, display_field: str) -> None:
        MasterCatalogWindow(self.window, title, file_path, key, display_field)

    def open_sustancias(self) -> None:
        SubstanceMasterWindow(self.window)

    def open_ubicacion(self) -> None:
        LocationMasterWindow(self.window)

    def open_from_label(self, label: str) -> None:
        mapping = {
            "Sustancias": self.open_sustancias,
            "T. Entrada": lambda: self.open_catalog("T. Entrada", TIPOS_ENTRADA_FILE, "maestrasTiposEntrada", "nombre"),
            "T. Salida": lambda: self.open_catalog("T. Salida", TIPOS_SALIDA_FILE, "maestrasTiposSalida", "nombre"),
            "Proveedor": lambda: self.open_catalog("Proveedor", PROVEEDORES_FILE, "maestrasProveedores", "nombre"),
            "C. Almace": lambda: self.open_catalog("C. Almace", ALMACENES_FILE, "maestrasAlmacenes", "nombre"),
            "Unidad": lambda: self.open_catalog("Unidad", UNIDADES_FILE, "maestrasUnidades", "nombre"),
            "Ubicacion": self.open_ubicacion,
            "Cond. Almac.": lambda: self.open_catalog("Cond. Almac.", CONDICIONES_FILE, "maestrasCondicionesAlmacenamiento", "nombre"),
        }
        action = mapping.get(label)
        if action:
            action()


class SubstanceMasterWindow:
    """Catálogo de sustancias con edición y estado habilitada/inhabilitada."""

    def __init__(self, parent: tk.Toplevel):
        self.window = tk.Toplevel(parent)
        self.window.title("Maestra de Sustancia")
        self.window.geometry("1180x620")
        self.window.configure(bg=COLORS["secondary"])

        self.control_var = tk.StringVar(value="No")
        self.estado_var = tk.StringVar(value="HABILITADA")
        self.location_var = tk.StringVar()
        self.inputs: dict[str, tk.Entry] = {}
        self.listbox: tk.Listbox | None = None
        self.selected_id: int | None = None
        self.sustancias: list[dict] = []
        self.stock_info_var = tk.StringVar(value="Stock actual: 0")
        self.ubicacion_combo: ttk.Combobox | None = None

        self._load_location_catalogs()

        self._build_ui()
        self.reload_items()

    def _load_location_catalogs(self) -> None:
        almacenes = DataHandler.load_json(ALMACENES_FILE).get("maestrasAlmacenes", [])
        ubicaciones = DataHandler.load_json(UBICACIONES_FILE).get("maestrasUbicaciones", [])
        ubicaciones_uso = DataHandler.load_json(UBICACIONES_USO_FILE).get("maestrasUbicacionesUso", [])
        self.almacen_lkp = Lookups(almacenes=almacenes)
        self.locations_by_key, self.location_by_name = build_location_indexes(ubicaciones, ubicaciones_uso)
        self.location_options = [
            r.get("nombre", "")
            for r in (ubicaciones + ubicaciones_uso)
            if r.get("nombre")
        ]

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

        content = tk.Frame(shell, bg="white")
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=2)
        content.columnconfigure(1, weight=3)

        left = tk.LabelFrame(content, text="Sustancias registradas", bg="white", fg=COLORS["text_dark"], font=("Segoe UI", 10, "bold"))
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        list_wrap = tk.Frame(left, bg="white")
        list_wrap.pack(fill="both", expand=True, padx=8, pady=8)

        self.listbox = tk.Listbox(list_wrap, font=("Segoe UI", 10))
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(list_wrap, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.configure(yscrollcommand=scrollbar.set)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        right = tk.LabelFrame(content, text="Detalle de la sustancia", bg="white", fg=COLORS["text_dark"], font=("Segoe UI", 10, "bold"))
        right.grid(row=0, column=1, sticky="nsew")

        grid = tk.Frame(right, bg="white")
        grid.pack(fill="both", expand=True, padx=8, pady=8)

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
        control_box.grid(row=1, column=0, sticky="ew", padx=8, pady=8)
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
        self._add_field(grid, "Cantidad Minima Stock", 2, 0)

        ubicacion_frame = tk.Frame(grid, bg="white")
        ubicacion_frame.grid(row=4, column=1, sticky="ew", padx=8, pady=(4, 0))
        tk.Label(ubicacion_frame, text="Ubicacion", bg="white", fg=COLORS["text_dark"], font=("Segoe UI", 11)).pack(anchor="w")
        self.ubicacion_combo = ttk.Combobox(
            ubicacion_frame,
            textvariable=self.location_var,
            values=self.location_options,
            state="readonly",
            font=("Segoe UI", 11),
        )
        self.ubicacion_combo.pack(fill="x", pady=(3, 4))

        estado_frame = tk.Frame(grid, bg="white")
        estado_frame.grid(row=4, column=2, sticky="ew", padx=8, pady=(8, 0))
        tk.Label(estado_frame, text="Estado", bg="white", fg=COLORS["text_dark"], font=("Segoe UI", 11)).pack(anchor="w")
        tk.Label(estado_frame, textvariable=self.estado_var, bg="white", fg=COLORS["primary"], font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(3, 0))
        tk.Label(estado_frame, textvariable=self.stock_info_var, bg="white", fg=COLORS["text_dark"], font=("Segoe UI", 10)).pack(anchor="w", pady=(4, 0))

        for col in range(3):
            grid.columnconfigure(col, weight=1)

        buttons = tk.Frame(shell, bg="white")
        buttons.pack(fill="x", pady=(10, 0))

        tk.Button(
            buttons,
            text="Nuevo",
            command=self._clear_form,
            bg=COLORS["border"],
            fg=COLORS["text_dark"],
            relief="flat",
            font=("Segoe UI", 11, "bold"),
            padx=20,
            pady=8,
        ).pack(side="left")

        tk.Button(
            buttons,
            text="Actualizar",
            command=self.update_selected,
            bg=COLORS["primary"],
            fg=COLORS["text_light"],
            relief="flat",
            font=("Segoe UI", 11, "bold"),
            padx=20,
            pady=8,
        ).pack(side="left", padx=(10, 0))

        tk.Button(
            buttons,
            text="Habilitar",
            command=self.habilitar_selected,
            bg=COLORS["success"],
            fg=COLORS["text_light"],
            relief="flat",
            font=("Segoe UI", 11, "bold"),
            padx=20,
            pady=8,
        ).pack(side="left", padx=(10, 0))

        tk.Button(
            buttons,
            text="Inhabilitar",
            command=self.inhabilitar_selected,
            bg=COLORS["error"],
            fg=COLORS["text_light"],
            relief="flat",
            font=("Segoe UI", 11, "bold"),
            padx=20,
            pady=8,
        ).pack(side="left", padx=(10, 0))

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

    def _normalize_sustancia(self, record: dict) -> dict:
        if "habilitada" not in record:
            record["habilitada"] = True
        record.pop("concentracion", None)
        record.pop("densidad", None)
        return record

    def _estado_text(self, record: dict) -> str:
        return "HABILITADA" if record.get("habilitada", True) else "INHABILITADA"

    def _list_text(self, record: dict) -> str:
        return f"{record.get('codigo', '')} - {record.get('nombre', '')} [{self._estado_text(record)}]"

    def _stock_total_sustancia(self, substance_id: int | None) -> float:
        total = 0.0
        if substance_id is None:
            return total
        inventario = DataHandler.load_json(INVENTARIO_FILE).get("inventario", [])
        for rec in inventario:
            if rec.get("id_sustancia") != substance_id:
                continue
            try:
                total += float(rec.get("stock", 0) or 0)
            except (TypeError, ValueError):
                continue
        return round(total, 6)

    def reload_items(self) -> None:
        data = DataHandler.load_json(SUSTANCIAS_FILE)
        raw = data.get("maestrasSustancias", [])
        self.sustancias = [self._normalize_sustancia(dict(r)) for r in raw]

        if self.listbox is None:
            return

        self.listbox.delete(0, tk.END)
        for rec in self.sustancias:
            self.listbox.insert(tk.END, self._list_text(rec))

    def _on_select(self, _event=None) -> None:
        if self.listbox is None:
            return
        selected = self.listbox.curselection()
        if not selected:
            return

        rec = self.sustancias[selected[0]]
        self.selected_id = rec.get("id")

        self.inputs["Codigo"].delete(0, tk.END)
        self.inputs["Codigo"].insert(0, str(rec.get("codigo", "")))
        self.inputs["Nombre del Producto"].delete(0, tk.END)
        self.inputs["Nombre del Producto"].insert(0, str(rec.get("nombre", "")))
        self.inputs["Codigo CAS"].delete(0, tk.END)
        self.inputs["Codigo CAS"].insert(0, str(rec.get("codigo_cas", "")))
        self.inputs["Limite Minimo de Control"].delete(0, tk.END)
        self.inputs["Limite Minimo de Control"].insert(0, str(rec.get("limite_minimo_control", "")))
        self.inputs["Codigo Sistema"].delete(0, tk.END)
        self.inputs["Codigo Sistema"].insert(0, str(rec.get("codigo_sistema", "")))
        self.inputs["Cantidad Minima Stock"].delete(0, tk.END)
        self.inputs["Cantidad Minima Stock"].insert(0, str(rec.get("cantidad_minima_stock", "")))
        self.location_var.set(location_name(rec, self.locations_by_key))

        self.control_var.set(str(rec.get("controlada", "No")) or "No")
        self.estado_var.set(self._estado_text(rec))
        self.stock_info_var.set(f"Stock actual: {self._stock_total_sustancia(rec.get('id'))}")

    def _clear_form(self) -> None:
        self.selected_id = None
        for input_entry in self.inputs.values():
            input_entry.delete(0, tk.END)
        self.control_var.set("No")
        self.location_var.set("")
        self.estado_var.set("HABILITADA")
        self.stock_info_var.set("Stock actual: 0")
        if self.listbox is not None:
            self.listbox.selection_clear(0, tk.END)

    def _selected_location_fields(self) -> tuple[str, int | None]:
        selected = self.location_var.get().strip()
        if not selected:
            return "", None
        for key, record in self.locations_by_key.items():
            if str(record.get("nombre", "")).strip() == selected:
                return key[0], key[1]
        return "", None

    def _log_estado_change(self, codigo: str, old_estado: str, new_estado: str) -> None:
        registrar_bitacora(
            usuario="Sistema",
            tipo_operacion="Actualización",
            hoja="Sustancias",
            id_registro=codigo,
            campo="habilitada",
            valor_anterior=old_estado,
            valor_nuevo=new_estado,
        )

    def save(self) -> None:
        original_cursor = self.window.cget("cursor")
        self.window.config(cursor="watch")
        self.window.update()
        codigo = self.inputs["Codigo"].get().strip()
        nombre = self.inputs["Nombre del Producto"].get().strip()

        if not codigo or not nombre:
            messagebox.showerror("Validacion", "Codigo y Nombre del Producto son obligatorios")
            self.window.config(cursor=original_cursor)
            return

        data = DataHandler.load_json(SUSTANCIAS_FILE)
        sustancias = data.get("maestrasSustancias", [])

        if any(item.get("codigo") == codigo for item in sustancias):
            messagebox.showerror("Validacion", "Ya existe una sustancia con ese codigo")
            self.window.config(cursor=original_cursor)
            return

        ubicacion_tipo, id_ubicacion = self._selected_location_fields()

        record = {
            "codigo": codigo,
            "nombre": nombre,
            "codigo_cas": self.inputs["Codigo CAS"].get().strip(),
            "controlada": self.control_var.get(),
            "limite_minimo_control": self.inputs["Limite Minimo de Control"].get().strip(),
            "codigo_sistema": self.inputs["Codigo Sistema"].get().strip(),
            "cantidad_minima_stock": self.inputs["Cantidad Minima Stock"].get().strip(),
            "ubicacion_tipo": ubicacion_tipo,
            "id_ubicacion": id_ubicacion,
            "id_unidad": None,
            "habilitada": True,
        }

        if not DataHandler.add_record(SUSTANCIAS_FILE, "maestrasSustancias", record):
            messagebox.showerror("Error", "No se pudo guardar la sustancia")
            self.window.config(cursor=original_cursor)
            return

        messagebox.showinfo("Exito", "Sustancia guardada correctamente")
        registrar_bitacora(
            usuario="Sistema",
            tipo_operacion="Inserción",
            hoja="Sustancias",
            id_registro=codigo,
            campo="estado",
            valor_anterior="",
            valor_nuevo="HABILITADA",
        )
        self._clear_form()
        self.reload_items()
        self.window.config(cursor=original_cursor)

    def update_selected(self) -> None:
        if self.selected_id is None:
            messagebox.showwarning("Aviso", "Selecciona una sustancia para actualizar")
            return

        codigo = self.inputs["Codigo"].get().strip()
        nombre = self.inputs["Nombre del Producto"].get().strip()
        if not codigo or not nombre:
            messagebox.showerror("Validacion", "Codigo y Nombre del Producto son obligatorios")
            return

        data = DataHandler.load_json(SUSTANCIAS_FILE)
        sustancias = data.get("maestrasSustancias", [])

        target = None
        for rec in sustancias:
            if rec.get("id") == self.selected_id:
                target = rec
                break

        if target is None:
            messagebox.showerror("Error", "No se encontró la sustancia seleccionada")
            return

        for rec in sustancias:
            if rec.get("id") != self.selected_id and str(rec.get("codigo", "")).strip() == codigo:
                messagebox.showerror("Validacion", "Ya existe otra sustancia con ese codigo")
                return

        ubicacion_tipo, id_ubicacion = self._selected_location_fields()

        target.update({
            "codigo": codigo,
            "nombre": nombre,
            "codigo_cas": self.inputs["Codigo CAS"].get().strip(),
            "controlada": self.control_var.get(),
            "limite_minimo_control": self.inputs["Limite Minimo de Control"].get().strip(),
            "codigo_sistema": self.inputs["Codigo Sistema"].get().strip(),
            "cantidad_minima_stock": self.inputs["Cantidad Minima Stock"].get().strip(),
            "ubicacion_tipo": ubicacion_tipo,
            "id_ubicacion": id_ubicacion,
            "habilitada": bool(target.get("habilitada", True)),
        })

        if not DataHandler.save_json(SUSTANCIAS_FILE, data):
            messagebox.showerror("Error", "No se pudo actualizar la sustancia")
            return

        registrar_bitacora(
            usuario="Sistema",
            tipo_operacion="Actualización",
            hoja="Sustancias",
            id_registro=codigo,
            campo="datos_maestra",
            valor_anterior="",
            valor_nuevo="Actualizada",
        )
        messagebox.showinfo("Exito", "Sustancia actualizada correctamente")
        self.reload_items()

    def habilitar_selected(self) -> None:
        self._toggle_estado(True)

    def inhabilitar_selected(self) -> None:
        self._toggle_estado(False)

    def _toggle_estado(self, habilitar: bool) -> None:
        if self.selected_id is None:
            messagebox.showwarning("Aviso", "Selecciona una sustancia")
            return

        data = DataHandler.load_json(SUSTANCIAS_FILE)
        sustancias = data.get("maestrasSustancias", [])

        target = None
        for rec in sustancias:
            if rec.get("id") == self.selected_id:
                target = rec
                break

        if target is None:
            messagebox.showerror("Error", "No se encontró la sustancia seleccionada")
            return

        codigo = str(target.get("codigo", "")).strip()
        estado_actual = bool(target.get("habilitada", True))
        if estado_actual == habilitar:
            messagebox.showinfo("Aviso", f"La sustancia ya está {'habilitada' if habilitar else 'inhabilitada'}")
            return

        if not habilitar:
            stock = self._stock_total_sustancia(target.get("id"))
            if stock > 0:
                messagebox.showwarning(
                    "Regla de negocio",
                    "No se puede inhabilitar una sustancia con stock disponible.",
                )
                return

        old_estado = "HABILITADA" if estado_actual else "INHABILITADA"
        new_estado = "HABILITADA" if habilitar else "INHABILITADA"
        target["habilitada"] = habilitar

        if not DataHandler.save_json(SUSTANCIAS_FILE, data):
            messagebox.showerror("Error", "No se pudo actualizar el estado")
            return

        self._log_estado_change(codigo, old_estado, new_estado)
        messagebox.showinfo("Exito", f"Sustancia {new_estado.lower()} correctamente")
        self.reload_items()
        self._on_select()


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

        if self.key == "maestrasUnidades":
            payload = {"codigo": name.lower(), "nombre": name}
        elif self.key == "maestrasUbicaciones":
            payload = {"codigo": f"UB{str(self.listbox.size() + 1).zfill(3)}", "nombre": name, "id_almacen": None}

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

        if not messagebox.askyesno("Confirmar", f"¿Desea eliminar '{selected_name}'?"):
            return

        data = DataHandler.load_json(self.file_path)
        records = data.get(self.key, [])

        filtered = [r for r in records if r.get(self.display_field, "") != selected_name]
        data[self.key] = filtered

        if not DataHandler.save_json(self.file_path, data):
            messagebox.showerror("Error", "No se pudo eliminar el registro")
            return

        self.reload_items()


class LocationMasterWindow:
    """Catálogo dual de ubicaciones: Ubicación y Ubicación de Uso."""

    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Maestra - Ubicaciones")
        self.window.geometry("700x480")
        self.window.configure(bg=COLORS["secondary"])
        self.tipo_var = tk.StringVar(value="ubicacion")
        self.almacen_var = tk.StringVar()
        self.ubicaciones_records: list[dict] = []
        self.uso_records: list[dict] = []
        self.almacen_combo: ttk.Combobox | None = None
        self._build_ui()
        self._reload_all()

    def _build_ui(self) -> None:
        card = tk.Frame(self.window, bg="white", bd=1, relief="solid", padx=14, pady=14)
        card.pack(expand=True, fill="both", padx=14, pady=14)

        tk.Label(
            card, text="Catálogo: Ubicaciones",
            bg="white", fg=COLORS["text_dark"],
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w", pady=(0, 10))

        # ── Tipo de ubicación ──
        tipo_frame = tk.LabelFrame(card, text="Tipo de ubicación", bg="white",
                                   fg=COLORS["text_dark"], font=("Segoe UI", 10))
        tipo_frame.pack(fill="x", pady=(0, 8))

        tk.Radiobutton(
            tipo_frame, text="Ubicación", variable=self.tipo_var,
            value="ubicacion", bg="white", font=("Segoe UI", 10, "bold"),
        ).pack(side="left", padx=16, pady=4)
        tk.Radiobutton(
            tipo_frame, text="Ubicación de Uso", variable=self.tipo_var,
            value="ubicacion_uso", bg="white", font=("Segoe UI", 10, "bold"),
        ).pack(side="left", padx=16, pady=4)

        # ── Entrada + botón agregar ──
        entry_row = tk.Frame(card, bg="white")
        entry_row.pack(fill="x", pady=(0, 8))

        self.name_entry = tk.Entry(entry_row, font=("Segoe UI", 11))
        self.name_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        tk.Button(
            entry_row, text="Agregar", bg=COLORS["primary"],
            fg=COLORS["text_light"], relief="flat", command=self._add_item,
        ).pack(side="left")

        almacen_row = tk.Frame(card, bg="white")
        almacen_row.pack(fill="x", pady=(0, 8))
        tk.Label(almacen_row, text="Almacén", bg="white", fg=COLORS["text_dark"], font=("Segoe UI", 10)).pack(side="left", padx=(0, 8))
        almacenes = DataHandler.load_json(ALMACENES_FILE).get("maestrasAlmacenes", [])
        self.almacen_lkp = Lookups(almacenes=almacenes)
        self.almacen_combo = ttk.Combobox(
            almacen_row,
            textvariable=self.almacen_var,
            values=[r.get("nombre", "") for r in almacenes if r.get("nombre")],
            state="readonly",
        )
        self.almacen_combo.pack(side="left", fill="x", expand=True)

        # ── Listas lado a lado ──
        lists_frame = tk.Frame(card, bg="white")
        lists_frame.pack(fill="both", expand=True, pady=(0, 8))

        # Ubicaciones
        left = tk.LabelFrame(lists_frame, text="Ubicaciones", bg="white",
                             fg=COLORS["text_dark"], font=("Segoe UI", 10, "bold"))
        left.pack(side="left", fill="both", expand=True, padx=(0, 4))
        self.list_ubicacion = tk.Listbox(left, height=10)
        self.list_ubicacion.pack(fill="both", expand=True, padx=4, pady=4)

        # Ubicaciones de Uso
        right = tk.LabelFrame(lists_frame, text="Ubicaciones de Uso", bg="white",
                              fg=COLORS["text_dark"], font=("Segoe UI", 10, "bold"))
        right.pack(side="left", fill="both", expand=True, padx=(4, 0))
        self.list_uso = tk.Listbox(right, height=10)
        self.list_uso.pack(fill="both", expand=True, padx=4, pady=4)

        # ── Botones de acción ──
        action_row = tk.Frame(card, bg="white")
        action_row.pack(fill="x")

        tk.Button(
            action_row, text="Eliminar seleccionado", bg=COLORS["error"],
            fg=COLORS["text_light"], relief="flat", command=self._delete_selected,
        ).pack(side="left")

        tk.Button(
            action_row, text="Actualizar", bg=COLORS["border"],
            fg=COLORS["text_dark"], relief="flat", command=self._reload_all,
        ).pack(side="right")

    def _reload_all(self) -> None:
        self.ubicaciones_records = DataHandler.load_json(UBICACIONES_FILE).get("maestrasUbicaciones", [])
        self.uso_records = DataHandler.load_json(UBICACIONES_USO_FILE).get("maestrasUbicacionesUso", [])

        self.list_ubicacion.delete(0, tk.END)
        for r in self.ubicaciones_records:
            name = r.get("nombre", "")
            if name:
                almacen = self.almacen_lkp.to_name("almacenes", r.get("id_almacen"))
                self.list_ubicacion.insert(tk.END, f"{name} | {almacen}" if almacen else name)

        self.list_uso.delete(0, tk.END)
        for r in self.uso_records:
            name = r.get("nombre", "")
            if name:
                self.list_uso.insert(tk.END, name)

    def _add_item(self) -> None:
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Validación", "Ingresa un nombre para agregar")
            return

        tipo = self.tipo_var.get()
        if tipo == "ubicacion":
            file_path = UBICACIONES_FILE
            key = "maestrasUbicaciones"
            existing = DataHandler.load_json(file_path).get(key, [])
            almacen = self.almacen_var.get().strip()
            if not almacen:
                messagebox.showerror("Validación", "Selecciona un almacén para la ubicación")
                return
            payload = {
                "codigo": f"UB{str(len(existing) + 1).zfill(3)}",
                "nombre": name,
                "id_almacen": self.almacen_lkp.to_id("almacenes", almacen),
            }
        else:
            file_path = UBICACIONES_USO_FILE
            key = "maestrasUbicacionesUso"
            payload = {"nombre": name}

        # Verificar duplicados
        existing = DataHandler.load_json(file_path).get(key, [])
        if any(r.get("nombre", "").lower() == name.lower() for r in existing):
            messagebox.showwarning("Duplicado", f"Ya existe '{name}' en este catálogo")
            return

        if not DataHandler.add_record(file_path, key, payload):
            messagebox.showerror("Error", "No se pudo guardar el registro")
            return

        self.name_entry.delete(0, tk.END)
        self._reload_all()

    def _delete_selected(self) -> None:
        # Intentar desde ambas listas
        sel_ub = self.list_ubicacion.curselection()
        sel_uso = self.list_uso.curselection()

        if sel_ub:
            selected = self.ubicaciones_records[sel_ub[0]]
            selected_name = selected.get("nombre", "")
            file_path = UBICACIONES_FILE
            key = "maestrasUbicaciones"
            target_id = selected.get("id")
        elif sel_uso:
            selected = self.uso_records[sel_uso[0]]
            selected_name = selected.get("nombre", "")
            file_path = UBICACIONES_USO_FILE
            key = "maestrasUbicacionesUso"
            target_id = selected.get("id")
        else:
            messagebox.showwarning("Aviso", "Selecciona un item de cualquiera de las listas")
            return

        if not messagebox.askyesno("Confirmar", f"¿Desea eliminar '{selected_name}'?"):
            return

        data = DataHandler.load_json(file_path)
        records = data.get(key, [])
        data[key] = [r for r in records if r.get("id") != target_id]

        if not DataHandler.save_json(file_path, data):
            messagebox.showerror("Error", "No se pudo eliminar el registro")
            return

        self._reload_all()
