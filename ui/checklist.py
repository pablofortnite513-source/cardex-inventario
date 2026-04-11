import tkinter as tk
import importlib
from datetime import date
from tkinter import messagebox, ttk
from pathlib import Path

from tkcalendar import DateEntry

from config.config import CHECKLISTS_FILE, COLORS, PROVEEDORES_FILE, SUSTANCIAS_FILE, USERS_FILE
from ui.input_behaviors import bind_code_combo_autofill, bind_uppercase
from utils.data_handler import DataHandler, Lookups, build_substance_indexes, substance_from_code

CHECK_ITEMS = [
    "Nombre",
    "No. de Lote",
    "Cantidad",
    "Rótulo de Identificación",
    "Fecha de Fabricación",
    "Fecha de Vencimiento",
    "Fabricante",
    "Rótulos de seguridad, sellos y precintos de seguridad y garantía",
    "Ficha de Seguridad",
    "Certificado de Calidad",
    "Se evidencian Golpes, Roturas u Otros",
    "Cumple con las especificaciones requeridas",
]


class CheckListWindow:
    """Lista de chequeo de recepción de compra."""

    def __init__(self, parent: tk.Tk, usuario: str = "", on_saved=None):
        self.window = tk.Toplevel(parent)
        self.window.title("Lista de Chequeo - Recepción de Compra")
        self.window.geometry("1180x820")
        self.window.configure(bg=COLORS["secondary"])
        self.usuario = usuario
        self.on_saved = on_saved

        self.fecha_recepcion_var = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        self.proveedor_var = tk.StringVar()
        self.orden_compra_var = tk.StringVar()
        self.codigo_var = tk.StringVar()
        self.lote_var = tk.StringVar()
        self.cantidad_var = tk.StringVar()
        self.observacion_producto_var = tk.StringVar()
        self.nombre_var = tk.StringVar()
        self.aprobo_var = tk.StringVar()
        self.verifico_var = tk.StringVar()

        self.observaciones_text: tk.Text | None = None
        self.check_vars: dict[str, tk.StringVar] = {item: tk.StringVar(value="NONE") for item in CHECK_ITEMS}
        self._combo_sources: dict[str, list[str]] = {}
        self._signature_images: list = []
        self._aprobo_preview: tk.Label | None = None
        self._verifico_preview: tk.Label | None = None

        proveedores = DataHandler.load_json(PROVEEDORES_FILE).get("maestrasProveedores", [])
        sustancias = DataHandler.load_json(SUSTANCIAS_FILE).get("maestrasSustancias", [])
        self.lkp = Lookups(proveedores=proveedores)
        self.sustancias_by_id, self.sustancias_by_code = build_substance_indexes(sustancias)

        self.proveedor_options = [r.get("nombre", "") for r in proveedores if r.get("nombre")]
        self.codigo_options = [
            str(r.get("codigo", "")).strip()
            for r in sustancias
            if str(r.get("codigo", "")).strip() and bool(r.get("habilitada", True))
        ]
        self.codigo_options = sorted(self.codigo_options)

        usuarios = DataHandler.get_all(USERS_FILE, "usuarios")
        self.signature_users = [u for u in usuarios if str(u.get("firma_path", "")).strip()]
        self.signature_name_to_user = {
            str(u.get("nombre", "")).strip(): u
            for u in self.signature_users
            if str(u.get("nombre", "")).strip()
        }
        self.signature_names = sorted(self.signature_name_to_user.keys())

        if not CHECKLISTS_FILE.exists():
            DataHandler.save_json(CHECKLISTS_FILE, {"listasChequeoRecepcionCompra": []})

        self._build_ui()
        bind_uppercase(self.orden_compra_var)
        bind_uppercase(self.lote_var)
        bind_uppercase(self.observacion_producto_var)

    def _mb_showerror(self, *args, **kwargs):
        kwargs.setdefault("parent", self.window)
        return messagebox.showerror(*args, **kwargs)

    def _mb_showinfo(self, *args, **kwargs):
        kwargs.setdefault("parent", self.window)
        return messagebox.showinfo(*args, **kwargs)

    def _on_mousewheel(self, event) -> None:
        try:
            if self._canvas.winfo_exists():
                self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except tk.TclError:
            pass

    def _build_ui(self) -> None:
        outer = tk.Frame(self.window, bg="white", bd=1, relief="solid")
        outer.pack(expand=True, fill="both", padx=12, pady=12)

        self._canvas = tk.Canvas(outer, bg="white", highlightthickness=0)
        v_scroll = ttk.Scrollbar(outer, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=v_scroll.set)
        v_scroll.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        wrapper = tk.Frame(self._canvas, bg="white", padx=14, pady=14)
        wrapper.bind("<Configure>", lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas_window = self._canvas.create_window((0, 0), window=wrapper, anchor="nw")
        self._canvas.bind("<Configure>", lambda e: self._canvas.itemconfigure(self._canvas_window, width=e.width))
        self._canvas.bind("<Enter>", lambda e: self._canvas.bind_all("<MouseWheel>", self._on_mousewheel))
        self._canvas.bind("<Leave>", lambda e: self._canvas.unbind_all("<MouseWheel>"))

        tk.Label(
            wrapper,
            text="LISTA DE CHEQUEO RECEPCIÓN DE COMPRA",
            bg=COLORS["primary"],
            fg=COLORS["text_light"],
            font=("Segoe UI", 17, "bold"),
            pady=8,
        ).pack(fill="x", pady=(0, 10))

        top = tk.LabelFrame(wrapper, text="Datos de recepción", bg="white", fg="#1F4F8A", font=("Segoe UI", 10, "bold"))
        top.pack(fill="x", pady=(0, 8))

        row = tk.Frame(top, bg="white")
        row.pack(fill="x", padx=10, pady=8)

        self._add_date(row, "Fecha Recepción", self.fecha_recepcion_var, 0)
        self._add_combo(row, "Proveedor", self.proveedor_var, self.proveedor_options, 1)
        self._add_entry(row, "No. Orden de Compra", self.orden_compra_var, 2)

        producto = tk.LabelFrame(wrapper, text="Producto recibido", bg="white", fg="#1F4F8A", font=("Segoe UI", 10, "bold"))
        producto.pack(fill="x", pady=(0, 8))
        prow = tk.Frame(producto, bg="white")
        prow.pack(fill="x", padx=10, pady=8)

        self._codigo_combo = self._add_combo(prow, "Código Producto", self.codigo_var, self.codigo_options, 0, state="normal")
        self._add_entry(prow, "Lote", self.lote_var, 1)
        self._add_entry(prow, "Cantidad", self.cantidad_var, 2)
        self._add_entry(prow, "Observación", self.observacion_producto_var, 3)
        self._add_entry(prow, "Nombre del Producto", self.nombre_var, 0, row=1, col_span=4, readonly=True)
        bind_code_combo_autofill(
            self._codigo_combo,
            lambda: self.codigo_options,
            self._set_codigo_data,
            self._clear_codigo_data,
        )
        check_frame = tk.LabelFrame(
            wrapper,
            text="Verificación de recepción de reactivo y sustancias de referencia",
            bg="white",
            fg="#1F4F8A",
            font=("Segoe UI", 10, "bold"),
        )
        check_frame.pack(fill="x", pady=(0, 8))

        for i, item in enumerate(CHECK_ITEMS):
            rowf = tk.Frame(check_frame, bg="white")
            rowf.pack(fill="x", padx=10, pady=2)
            tk.Label(rowf, text=item, bg="white", anchor="w").pack(side="left", fill="x", expand=True)
            tk.Radiobutton(rowf, text="Sí", value="SI", variable=self.check_vars[item], bg="white").pack(side="left", padx=(6, 10))
            tk.Radiobutton(rowf, text="No", value="NO", variable=self.check_vars[item], bg="white").pack(side="left")

        obs_frame = tk.Frame(wrapper, bg="white")
        obs_frame.pack(fill="x", pady=(0, 8))
        tk.Label(obs_frame, text="OBSERVACIONES:", bg="white", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.observaciones_text = tk.Text(obs_frame, height=4, font=("Segoe UI", 10))
        self.observaciones_text.pack(fill="x", pady=(4, 0))
        bind_uppercase(self.observaciones_text)

        rv = tk.LabelFrame(wrapper, text="Firmas", bg="white", fg="#1F4F8A", font=("Segoe UI", 10, "bold"))
        rv.pack(fill="x", pady=(0, 8))

        self._aprobo_combo = self._add_combo(rv, "Aprobó", self.aprobo_var, self.signature_names, 0)
        self._aprobo_combo.configure(state="readonly")
        self._aprobo_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_signature_selected("aprobo"))

        self._verifico_combo = self._add_combo(rv, "Verificó", self.verifico_var, self.signature_names, 1)
        self._verifico_combo.configure(state="readonly")
        self._verifico_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_signature_selected("verifico"))

        previews = tk.Frame(rv, bg="white")
        previews.grid(row=1, column=0, columnspan=2, sticky="ew", padx=8, pady=(8, 2))
        tk.Label(previews, text="Firma Aprobó", bg="white", fg="#333333").grid(row=0, column=0, sticky="w")
        tk.Label(previews, text="Firma Verificó", bg="white", fg="#333333").grid(row=0, column=1, sticky="w")
        aprobo_box = tk.Frame(previews, bg="#F7F7F7", relief="solid", bd=1, height=140)
        aprobo_box.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=(4, 0))
        aprobo_box.grid_propagate(False)
        self._aprobo_preview = tk.Label(aprobo_box, bg="#F7F7F7")
        self._aprobo_preview.pack(fill="both", expand=True)

        verifico_box = tk.Frame(previews, bg="#F7F7F7", relief="solid", bd=1, height=140)
        verifico_box.grid(row=1, column=1, sticky="nsew", pady=(4, 0))
        verifico_box.grid_propagate(False)
        self._verifico_preview = tk.Label(verifico_box, bg="#F7F7F7")
        self._verifico_preview.pack(fill="both", expand=True)
        previews.columnconfigure(0, weight=1)
        previews.columnconfigure(1, weight=1)
        previews.rowconfigure(1, weight=1)
        rv.columnconfigure(0, weight=1)
        rv.columnconfigure(1, weight=1)

        btns = tk.Frame(wrapper, bg="white")
        btns.pack(fill="x", pady=(4, 0))
        tk.Button(btns, text="Guardar", command=self.save, bg=COLORS["primary"], fg=COLORS["text_light"], relief="flat", padx=20, pady=6).pack(side="left", padx=(0, 8))
        tk.Button(btns, text="Limpiar", command=self.clear, bg=COLORS["border"], fg=COLORS["text_dark"], relief="flat", padx=20, pady=6).pack(side="left")
        tk.Button(btns, text="Salir", command=self.window.destroy, bg=COLORS["error"], fg=COLORS["text_light"], relief="flat", padx=20, pady=6).pack(side="right")

    def _add_date(self, parent: tk.Widget, label: str, var: tk.StringVar, col: int) -> None:
        frame = tk.Frame(parent, bg="white")
        frame.grid(row=0, column=col, padx=8, sticky="ew")
        tk.Label(frame, text=label, bg="white").pack(anchor="w")
        DateEntry(
            frame,
            textvariable=var,
            date_pattern="yyyy-mm-dd",
            background=COLORS["primary"],
            foreground="white",
            width=18,
        ).pack(fill="x", pady=(4, 0))
        parent.columnconfigure(col, weight=1)

    def _add_entry(self, parent: tk.Widget, label: str, var: tk.StringVar, col: int,
                   row: int = 0, col_span: int = 1, readonly: bool = False) -> tk.Entry:
        frame = tk.Frame(parent, bg="white")
        frame.grid(row=row, column=col, columnspan=col_span, padx=8, pady=(0, 4), sticky="ew")
        tk.Label(frame, text=label, bg="white").pack(anchor="w")
        state = "readonly" if readonly else "normal"
        entry = tk.Entry(frame, textvariable=var, state=state)
        entry.pack(fill="x", pady=(4, 0))
        parent.columnconfigure(col, weight=1)
        return entry

    def _add_combo(self, parent: tk.Widget, label: str, var: tk.StringVar, options: list[str],
                   col: int, row: int = 0, state: str = "readonly") -> ttk.Combobox:
        frame = tk.Frame(parent, bg="white")
        frame.grid(row=row, column=col, padx=8, pady=(0, 4), sticky="ew")
        tk.Label(frame, text=label, bg="white").pack(anchor="w")
        combo = ttk.Combobox(frame, textvariable=var, values=options, state=state)
        combo.pack(fill="x", pady=(4, 0))
        self._combo_sources[str(combo)] = [str(opt).strip() for opt in options if str(opt).strip()]
        parent.columnconfigure(col, weight=1)
        return combo

    def clear(self) -> None:
        self.fecha_recepcion_var.set(date.today().strftime("%Y-%m-%d"))
        self.proveedor_var.set("")
        self.orden_compra_var.set("")
        self.codigo_var.set("")
        self.nombre_var.set("")
        self.lote_var.set("")
        self.cantidad_var.set("")
        self.observacion_producto_var.set("")
        self.aprobo_var.set("")
        self.verifico_var.set("")
        if self._aprobo_preview is not None:
            self._aprobo_preview.configure(image="", text="")
        if self._verifico_preview is not None:
            self._verifico_preview.configure(image="", text="")
        for var in self.check_vars.values():
            var.set("NONE")
        if self.observaciones_text is not None:
            self.observaciones_text.delete("1.0", tk.END)

    def save(self) -> None:
        required = {
            "Fecha Recepción": self.fecha_recepcion_var.get().strip(),
            "Proveedor": self.proveedor_var.get().strip(),
            "Código Producto": self.codigo_var.get().strip(),
            "Lote": self.lote_var.get().strip(),
            "Cantidad": self.cantidad_var.get().strip(),
            "Aprobó": self.aprobo_var.get().strip(),
            "Verificó": self.verifico_var.get().strip(),
        }
        missing = [k for k, v in required.items() if not v]
        if missing:
            self._mb_showerror("Validación", f"Completa campos obligatorios: {', '.join(missing)}")
            return
        sin_marcar = [item for item in CHECK_ITEMS if self.check_vars[item].get() not in ("SI", "NO")]
        if sin_marcar:
            self._mb_showerror(
                "Validación",
                "Debes marcar Sí o No en todos los ítems del checklist.\n\nFaltan:\n- " + "\n- ".join(sin_marcar),
            )
            return


        try:
            cantidad = float(self.cantidad_var.get().strip().replace(",", "."))
        except ValueError:
            self._mb_showerror("Validación", "Cantidad debe ser numérica")
            return

        if cantidad <= 0:
            self._mb_showerror("Validación", "Cantidad debe ser mayor a 0")
            return

        selected_sustancia = substance_from_code(self.sustancias_by_code, self.codigo_var.get().strip())
        id_sustancia = selected_sustancia.get("id") if selected_sustancia else None

        proveedor_nombre = self.proveedor_var.get().strip()
        record = {
            "fecha_recepcion": self.fecha_recepcion_var.get().strip(),
            "id_proveedor": self.lkp.to_id("proveedores", proveedor_nombre),
            "orden_compra": self.orden_compra_var.get().strip(),
            "id_sustancia": id_sustancia,
            "codigo_producto": self.codigo_var.get().strip(),
            "lote": self.lote_var.get().strip(),
            "cantidad": cantidad,
            "observacion_producto": self.observacion_producto_var.get().strip(),
            "checklist": {item: self.check_vars[item].get().strip() for item in CHECK_ITEMS},
            "observaciones": self.observaciones_text.get("1.0", tk.END).strip() if self.observaciones_text else "",
            "aprobo": self.aprobo_var.get().strip(),
            "reviso": self.aprobo_var.get().strip(),
            "verifico": self.verifico_var.get().strip(),
            "usuario": self.usuario,
        }

        if not DataHandler.add_record(CHECKLISTS_FILE, "listasChequeoRecepcionCompra", record):
            self._mb_showerror("Error", "No se pudo guardar la lista de chequeo")
            return

        prefill = {
            "codigo": self.codigo_var.get().strip(),
            "lote": self.lote_var.get().strip(),
            "cantidad": str(cantidad),
            "proveedor": proveedor_nombre,
        }
        self._mb_showinfo("Éxito", "Lista de chequeo guardada correctamente")
        if self.on_saved:
            self.on_saved(prefill)
        self.window.destroy()

        if self.aprobo_var.get().strip() == self.verifico_var.get().strip():
            self._mb_showerror("Validación", "Aprobó y Verificó no pueden ser la misma persona")
            return

    def _set_codigo_data(self, code: str) -> None:
        self.codigo_var.set(code)
        sustancia = substance_from_code(self.sustancias_by_code, code)
        self.nombre_var.set(str(sustancia.get("nombre", "")) if sustancia else "")

    def _clear_codigo_data(self) -> None:
        self.nombre_var.set("")

    def _on_signature_selected(self, role: str) -> None:
        name = self.aprobo_var.get().strip() if role == "aprobo" else self.verifico_var.get().strip()
        user = self.signature_name_to_user.get(name)
        if user is None:
            return

        password = self._ask_signature_password(name)
        if password is None:
            if role == "aprobo":
                self.aprobo_var.set("")
            else:
                self.verifico_var.set("")
            return

        expected = str(user.get("firma_password", "")).strip()
        if password != expected:
            messagebox.showerror("Firma", "Contraseña de firma incorrecta", parent=self.window)
            if role == "aprobo":
                self.aprobo_var.set("")
                if self._aprobo_preview is not None:
                    self._aprobo_preview.configure(image="", text="")
            else:
                self.verifico_var.set("")
                if self._verifico_preview is not None:
                    self._verifico_preview.configure(image="", text="")
            return
        
        target_label = self._aprobo_preview if role == "aprobo" else self._verifico_preview
        if target_label is not None:
            self._render_signature_preview(target_label, str(user.get("firma_path", "")))
        
        self._update_signature_combos()
    
    def _update_signature_combos(self) -> None:
        aprobo = self.aprobo_var.get().strip()
        verifico = self.verifico_var.get().strip()

        aprobo_options = [n for n in self.signature_names if n != verifico]
        verifico_options = [n for n in self.signature_names if n != aprobo]

        self._aprobo_combo["values"] = aprobo_options
        self._verifico_combo["values"] = verifico_options

    def _ask_signature_password(self, name: str) -> str | None:
        top = tk.Toplevel(self.window)
        top.title("Validar firma")
        top.geometry("360x150")
        top.configure(bg="white")
        top.transient(self.window)
        top.grab_set()

        result = {"value": None}
        var = tk.StringVar()

        tk.Label(top, text=f"Contraseña de firma para: {name}", bg="white").pack(anchor="w", padx=12, pady=(12, 4))
        entry = tk.Entry(top, textvariable=var, show="*")
        entry.pack(fill="x", padx=12, pady=(0, 10))
        entry.focus_set()

        btns = tk.Frame(top, bg="white")
        btns.pack(fill="x", padx=12, pady=(0, 8))

        def _ok() -> None:
            result["value"] = var.get().strip()
            top.destroy()

        def _cancel() -> None:
            top.destroy()

        tk.Button(btns, text="Aceptar", command=_ok, bg=COLORS["primary"], fg=COLORS["text_light"], relief="flat", padx=10, pady=4).pack(side="left")
        tk.Button(btns, text="Cancelar", command=_cancel, bg=COLORS["border"], fg=COLORS["text_dark"], relief="flat", padx=10, pady=4).pack(side="left", padx=(8, 0))

        top.wait_window()
        return result["value"]

    def _render_signature_preview(self, label: tk.Label, image_path: str) -> None:
        path = Path(image_path)
        if not path.exists():
            label.configure(image="", text="Sin archivo", fg="#666666")
            return

        try:
            image_mod = importlib.import_module("PIL.Image")
            image_tk_mod = importlib.import_module("PIL.ImageTk")
            img = image_mod.open(path)
            resampling = getattr(image_mod, "Resampling", None)
            method = resampling.LANCZOS if resampling else image_mod.LANCZOS

            # Ajustar la firma al tamaño real del recuadro azul
            label.update_idletasks()
            box_w = max(label.winfo_width(), 700)
            # Escalar proporcionalmente usando el ancho
            w_percent = (box_w - 8) / float(img.size[0])
            new_h = int(float(img.size[1]) * w_percent)

            img = img.resize((box_w - 8, new_h), method)
            max_h = 120
            if new_h > max_h:
                h_percent = max_h / float(img.size[1])
                new_w = int(float(img.size[0]) * h_percent)
                img = img.resize((new_w, max_h), method)

            img_tk = image_tk_mod.PhotoImage(img)
            self._signature_images.append(img_tk)
            label.configure(image=img_tk, text="")
        except Exception:
            label.configure(image="", text="No se pudo cargar", fg="#666666")
