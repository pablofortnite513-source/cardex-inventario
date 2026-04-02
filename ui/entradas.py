import tkinter as tk
from datetime import date, datetime
from tkinter import messagebox
from tkinter import ttk

from tkcalendar import DateEntry

from config.config import (
    COLORS,
    CONDICIONES_FILE,
    ENTRADAS_FILE,
    INVENTARIO_FILE,
    PROVEEDORES_FILE,
    SALIDAS_FILE,
    SUSTANCIAS_FILE,
    TIPOS_ENTRADA_FILE,
    UBICACIONES_FILE,
    UBICACIONES_USO_FILE,
    UNIDADES_FILE,
)
from ui.bitacora import registrar_bitacora
from ui.styles import apply_styles_to_window, make_required_label, apply_focus_bindings, build_header
from utils.data_handler import DataHandler, sync_inventario


class EntryFormWindow:
    """Formulario de entradas – lógica alineada al Excel Kardex."""

    def __init__(self, parent: tk.Tk, usuario: str = "", rol: str = ""):
        self.window = tk.Toplevel(parent)
        self.window.title("Sistema de Gestion - Entradas")
        self.window.geometry("1280x860")
        self.window.configure(bg=COLORS["secondary"])
        self.usuario = usuario
        self.rol = rol.lower()
        self.editing_id: int | None = None  # ID del registro en edición

        self.catalogs: dict[str, list[dict]] = {}

        self.tipo_entrada_var = tk.StringVar()
        self.fecha_entrada_var = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        self.codigo_var = tk.StringVar()
        self.nombre_var = tk.StringVar()
        self.lote_var = tk.StringVar()

        self.costo_unitario_var = tk.StringVar()
        self.costo_total_var = tk.StringVar(value="0")

        self.cantidad_var = tk.StringVar()
        self.presentacion_var = tk.StringVar()
        self.total_var = tk.StringVar()          # Editable – contenido neto real
        self.unidad_var = tk.StringVar()
        self.concentracion_var = tk.StringVar()
        self.densidad_var = tk.StringVar()
        self.proveedor_var = tk.StringVar()
        self.codigo_contable_var = tk.StringVar()

        self.certificado_var = tk.BooleanVar(value=False)
        self.msds_var = tk.BooleanVar(value=False)
        self.fecha_venc_var = tk.StringVar()
        self.fecha_doc_var = tk.StringVar()
        self.vigencia_doc_var = tk.StringVar()   # Fecha calculada (Fecha Doc + 5 años)

        self.ubicacion_var = tk.StringVar()
        self.condicion_var = tk.StringVar()

        self.tipo_combo: ttk.Combobox | None = None
        self.codigo_combo: ttk.Combobox | None = None
        self.unidad_combo: ttk.Combobox | None = None
        self.proveedor_combo: ttk.Combobox | None = None
        self.ubicacion_combo: ttk.Combobox | None = None
        self.condicion_combo: ttk.Combobox | None = None
        self.observaciones_text: tk.Text | None = None
        self.history_tree: ttk.Treeview | None = None
        self.save_btn: tk.Button | None = None
        self.costo_unitario_entry: tk.Entry | None = None

        self._load_catalogs()
        self._build_ui()
        self._bind_events()

    def _mb_showerror(self, *args, **kwargs):
        kwargs.setdefault("parent", self.window)
        return messagebox.showerror(*args, **kwargs)

    def _mb_showwarning(self, *args, **kwargs):
        kwargs.setdefault("parent", self.window)
        return messagebox.showwarning(*args, **kwargs)

    def _mb_showinfo(self, *args, **kwargs):
        kwargs.setdefault("parent", self.window)
        return messagebox.showinfo(*args, **kwargs)

    def _mb_askyesno(self, *args, **kwargs):
        kwargs.setdefault("parent", self.window)
        return messagebox.askyesno(*args, **kwargs)

    # ── catálogos ──────────────────────────────────────────────

    def _load_catalogs(self) -> None:
        tipos = DataHandler.load_json(TIPOS_ENTRADA_FILE).get("maestrasTiposEntrada", [])
        sustancias = DataHandler.load_json(SUSTANCIAS_FILE).get("maestrasSustancias", [])
        unidades = DataHandler.load_json(UNIDADES_FILE).get("maestrasUnidades", [])
        proveedores = DataHandler.load_json(PROVEEDORES_FILE).get("maestrasProveedores", [])
        ubicaciones = DataHandler.load_json(UBICACIONES_FILE).get("maestrasUbicaciones", [])
        ubicaciones_uso = DataHandler.load_json(UBICACIONES_USO_FILE).get("maestrasUbicacionesUso", [])
        condiciones = DataHandler.load_json(CONDICIONES_FILE).get("maestrasCondicionesAlmacenamiento", [])

        self.catalogs = {
            "tipos": tipos,
            "sustancias": sustancias,
            "unidades": unidades,
            "proveedores": proveedores,
            "ubicaciones": ubicaciones + ubicaciones_uso,
            "condiciones": condiciones,
        }

    # ── UI ─────────────────────────────────────────────────────

    def _on_mousewheel(self, event) -> None:
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _build_ui(self) -> None:
        outer = tk.Frame(self.window, bg="white", bd=1, relief="solid")
        outer.pack(expand=True, fill="both", padx=14, pady=14)

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

        build_header(wrapper, "Sistema de Gestión  -  Entradas")

        # ── fila superior: Info General + Costos ──
        top = tk.Frame(wrapper, bg="white")
        top.pack(fill="x", pady=(0, 10))
        top.columnconfigure(0, weight=4)
        top.columnconfigure(1, weight=1)

        general = tk.LabelFrame(top, text="Informacion General", bg="white", fg="#1F4F8A", font=("Segoe UI", 11, "bold"))
        general.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self.tipo_combo = self._add_combo(
            general, "Tipo Entrada", self.tipo_entrada_var,
            [x.get("nombre", "") for x in self.catalogs["tipos"] if x.get("nombre")], 0, 0,
            required=True,
        )
        self._add_date_entry(general, "Fecha Entrada", self.fecha_entrada_var, 0, 1, required=True)
        self.codigo_combo = self._add_combo(
            general, "Codigo", self.codigo_var, self._sustancia_codes(), 0, 2,
            required=True,
        )
        self._add_entry(general, "Lote", self.lote_var, 0, 3, required=True)
        self._add_entry(general, "Nombre del Producto", self.nombre_var, 1, 0, readonly=True, col_span=2)
        self._add_entry(general, "Codigo Contable", self.codigo_contable_var, 1, 2, readonly=True)

        costos = tk.LabelFrame(top, text="Costos", bg="white", fg="#1F4F8A", font=("Segoe UI", 11, "bold"))
        costos.grid(row=0, column=1, sticky="nsew")

        self.costo_unitario_entry = self._add_entry(costos, "Costo Unitario", self.costo_unitario_var, 0, 0)
        self._add_entry(costos, "Costo Total", self.costo_total_var, 0, 1, readonly=True)

        # ── fila media: Detalles + Documentación ──
        middle = tk.Frame(wrapper, bg="white")
        middle.pack(fill="x", pady=(0, 10))
        middle.columnconfigure(0, weight=3)
        middle.columnconfigure(1, weight=2)

        detalles = tk.LabelFrame(middle, text="Detalles del Producto", bg="white", fg="#1F4F8A", font=("Segoe UI", 11, "bold"))
        detalles.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self._add_entry(detalles, "Cantidad", self.cantidad_var, 0, 0, required=True)
        self._add_entry(detalles, "Presentacion", self.presentacion_var, 0, 1)
        # Total es calculado (readonly) = cantidad × presentación
        self._add_entry(detalles, "Total (contenido neto)", self.total_var, 0, 2, required=True, readonly=True)
        self.unidad_combo = self._add_combo(
            detalles, "Unidad", self.unidad_var,
            [x.get("nombre", "") for x in self.catalogs["unidades"] if x.get("nombre")], 0, 3,
            required=True,
        )
        self._add_entry(detalles, "Concentracion", self.concentracion_var, 0, 4)
        self._add_entry(detalles, "Densidad (g/mL)", self.densidad_var, 0, 5)
        self.proveedor_combo = self._add_combo(
            detalles, "Proveedor", self.proveedor_var,
            [x.get("nombre", "") for x in self.catalogs["proveedores"] if x.get("nombre")], 1, 0, col_span=5,
        )

        docs = tk.LabelFrame(middle, text="Documentacion Tecnica", bg="white", fg="#1F4F8A", font=("Segoe UI", 11, "bold"))
        docs.grid(row=0, column=1, sticky="nsew")

        checks = tk.Frame(docs, bg="white")
        checks.pack(fill="x", padx=10, pady=(8, 4))
        tk.Checkbutton(checks, text="Certificado", variable=self.certificado_var, bg="white").pack(side="left", padx=(0, 14))
        tk.Checkbutton(checks, text="MSDS", variable=self.msds_var, bg="white").pack(side="left")

        docs_grid = tk.Frame(docs, bg="white")
        docs_grid.pack(fill="x", padx=10, pady=(0, 10))
        self._add_date_entry(docs_grid, "Fecha Vencimiento", self.fecha_venc_var, 0, 0)
        self._add_date_entry(docs_grid, "Fecha Documento", self.fecha_doc_var, 0, 1)
        # Vigencia Documento = fecha (readonly, calculada como Fecha Doc + 5 años)
        self._add_entry(docs_grid, "Vigencia Documento", self.vigencia_doc_var, 0, 2, readonly=True)

        # ── Almacenamiento y Observaciones ──
        storage = tk.LabelFrame(wrapper, text="Almacenamiento y Observaciones", bg="white", fg="#1F4F8A", font=("Segoe UI", 11, "bold"))
        storage.pack(fill="x", pady=(0, 10))

        row_storage = tk.Frame(storage, bg="white")
        row_storage.pack(fill="x", padx=10, pady=10)

        self.ubicacion_combo = self._add_combo(
            row_storage, "Ubicacion", self.ubicacion_var,
            [x.get("nombre", "") for x in self.catalogs["ubicaciones"] if x.get("nombre")], 0, 0,
        )
        self.condicion_combo = self._add_combo(
            row_storage, "Condicion de Almacenamiento", self.condicion_var,
            [x.get("nombre", "") for x in self.catalogs["condiciones"] if x.get("nombre")], 0, 1,
        )

        obs_frame = tk.Frame(row_storage, bg="white")
        obs_frame.grid(row=0, column=2, sticky="nsew", padx=8)
        tk.Label(obs_frame, text="Observaciones", bg="white").pack(anchor="w")
        self.observaciones_text = tk.Text(obs_frame, height=3)
        self.observaciones_text.pack(fill="x", pady=(4, 0))

        row_storage.columnconfigure(0, weight=1)
        row_storage.columnconfigure(1, weight=2)
        row_storage.columnconfigure(2, weight=3)

        # ── Botones ──
        actions = tk.Frame(wrapper, bg="white")
        actions.pack(fill="x")

        self.save_btn = tk.Button(
            actions, text="Guardar", command=self.save,
            bg=COLORS["primary"], fg=COLORS["text_light"], relief="flat", padx=22, pady=7,
        )
        self.save_btn.pack(side="right", padx=(8, 0))
        tk.Button(
            actions, text="Limpiar", command=self.clear,
            bg=COLORS["primary"], fg=COLORS["text_light"], relief="flat", padx=22, pady=7,
        ).pack(side="right", padx=(8, 0))
        tk.Button(
            actions, text="Etiquetas", command=self.show_label_preview,
            bg="#111111", fg="white", relief="flat", padx=22, pady=7,
        ).pack(side="right", padx=(8, 0))
        tk.Button(
            actions, text="Salir", command=self.window.destroy,
            bg=COLORS["primary"], fg=COLORS["text_light"], relief="flat", padx=22, pady=7,
        ).pack(side="right")

        # ── Historial ──
        hist_frame = tk.LabelFrame(wrapper, text="Historial de Entradas", bg="white", fg="#1F4F8A", font=("Segoe UI", 11, "bold"))
        hist_frame.pack(fill="both", expand=True, pady=(8, 0))

        # Filtros
        self.hist_fecha_var = tk.StringVar()
        self.hist_codigo_var = tk.StringVar()
        self.hist_lote_var = tk.StringVar()

        filter_row = tk.Frame(hist_frame, bg="white")
        filter_row.pack(fill="x", padx=6, pady=(4, 2))

        tk.Label(filter_row, text="Fecha:", bg="white").pack(side="left")
        DateEntry(
            filter_row, textvariable=self.hist_fecha_var, date_pattern="yyyy-mm-dd",
            width=10, background=COLORS["primary"], foreground="white",
        ).pack(side="left", padx=(2, 8))
        self.hist_fecha_var.set("")

        tk.Label(filter_row, text="Código:", bg="white").pack(side="left")
        tk.Entry(filter_row, textvariable=self.hist_codigo_var, width=10).pack(side="left", padx=(2, 8))

        tk.Label(filter_row, text="Lote:", bg="white").pack(side="left")
        tk.Entry(filter_row, textvariable=self.hist_lote_var, width=10).pack(side="left", padx=(2, 8))

        tk.Button(
            filter_row, text="Filtrar", command=self._filter_history,
            bg=COLORS["primary"], fg="white", relief="flat", padx=12, pady=3,
        ).pack(side="left", padx=(4, 4))
        tk.Button(
            filter_row, text="Borrar filtros", command=self._clear_history_filters,
            bg=COLORS["border"], fg=COLORS["text_dark"], relief="flat", padx=12, pady=3,
        ).pack(side="left")

        hist_cols = ("id", "fecha", "codigo", "nombre", "lote", "total", "unidad", "estado")
        tree_container = tk.Frame(hist_frame, bg="white")
        tree_container.pack(fill="both", expand=True, padx=6, pady=(2, 4))

        self.history_tree = ttk.Treeview(tree_container, columns=hist_cols, show="headings", height=5)
        hist_scroll_y = ttk.Scrollbar(tree_container, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=hist_scroll_y.set)
        self.history_tree.pack(side="left", fill="both", expand=True)
        hist_scroll_y.pack(side="right", fill="y")

        for col, heading, width in [
            ("id", "ID", 40), ("fecha", "Fecha", 90), ("codigo", "Código", 80),
            ("nombre", "Nombre", 200), ("lote", "Lote", 100), ("total", "Total", 80),
            ("unidad", "Unidad", 70), ("estado", "Estado", 90),
        ]:
            self.history_tree.heading(col, text=heading)
            self.history_tree.column(col, width=width, anchor="w")

        self.history_tree.tag_configure("anulado", foreground="#999999")

        hist_btns = tk.Frame(hist_frame, bg="white")
        hist_btns.pack(fill="x", padx=6, pady=(0, 6))

        if self.rol == "admin":
            tk.Button(
                hist_btns, text="Editar seleccionado", command=self._edit_selected,
                bg="#1F4F8A", fg="white", relief="flat", padx=16, pady=5,
            ).pack(side="left", padx=(0, 8))
            tk.Button(
                hist_btns, text="Anular seleccionado", command=self._annul_selected,
                bg=COLORS["error"], fg="white", relief="flat", padx=16, pady=5,
            ).pack(side="left")

        tk.Button(
            hist_btns, text="Actualizar", command=self._load_history,
            bg=COLORS["border"], fg=COLORS["text_dark"], relief="flat", padx=16, pady=5,
        ).pack(side="right")

        self._load_history()

        apply_styles_to_window(self.window)

    # ── helpers de UI ──────────────────────────────────────────

    def _add_date_entry(
        self, parent: tk.Widget, label: str, variable: tk.StringVar,
        row: int, col: int, col_span: int = 1, required: bool = False,
    ) -> DateEntry:
        frame = tk.Frame(parent, bg="white")
        frame.grid(row=row, column=col, columnspan=col_span, padx=8, pady=8, sticky="ew")
        if required:
            make_required_label(frame, label).pack(anchor="w")
        else:
            tk.Label(frame, text=label, bg="white").pack(anchor="w")
        de = DateEntry(
            frame, textvariable=variable, date_pattern="yyyy-mm-dd",
            width=18, background=COLORS["primary"], foreground="white",
            headersbackground=COLORS["primary"], headersforeground="white",
        )
        de.pack(fill="x", pady=(4, 0))
        if not variable.get().strip():
            de.delete(0, tk.END)
        parent.columnconfigure(col, weight=1)
        return de

    def _add_entry(
        self, parent: tk.Widget, label: str, variable: tk.StringVar,
        row: int, col: int, readonly: bool = False, col_span: int = 1,
        required: bool = False,
    ) -> tk.Entry:
        frame = tk.Frame(parent, bg="white")
        frame.grid(row=row, column=col, columnspan=col_span, padx=8, pady=8, sticky="ew")
        if required:
            make_required_label(frame, label).pack(anchor="w")
        else:
            tk.Label(frame, text=label, bg="white").pack(anchor="w")
        state = "readonly" if readonly else "normal"
        entry = tk.Entry(frame, textvariable=variable, state=state)
        entry.pack(fill="x", pady=(4, 0))
        if not readonly:
            apply_focus_bindings(entry)
        parent.columnconfigure(col, weight=1)
        return entry

    def _add_combo(
        self, parent: tk.Widget, label: str, variable: tk.StringVar,
        options: list[str], row: int, col: int, col_span: int = 1,
        required: bool = False,
    ) -> ttk.Combobox:
        frame = tk.Frame(parent, bg="white")
        frame.grid(row=row, column=col, columnspan=col_span, padx=8, pady=8, sticky="ew")
        if required:
            make_required_label(frame, label).pack(anchor="w")
        else:
            tk.Label(frame, text=label, bg="white").pack(anchor="w")
        combo = ttk.Combobox(frame, textvariable=variable, values=options, state="readonly")
        combo.pack(fill="x", pady=(4, 0))
        parent.columnconfigure(col, weight=1)
        return combo

    # ── bindings ───────────────────────────────────────────────

    def _bind_events(self) -> None:
        if self.codigo_combo is not None:
            self.codigo_combo.bind("<<ComboboxSelected>>", self._on_codigo_selected)
        self.cantidad_var.trace_add("write", lambda *_: self._recalculate_costo_total())
        self.costo_unitario_var.trace_add("write", lambda *_: self._recalculate_costo_total())
        self.fecha_doc_var.trace_add("write", lambda *_: self._recalculate_vigencia())

        # Auto-cálculo total = cantidad * presentacion
        self.cantidad_var.trace_add("write", lambda *_: self._recalculate_total())
        self.presentacion_var.trace_add("write", lambda *_: self._recalculate_total())

        # Validación numérica (solo dígitos, punto, signo negativo; comas → puntos)
        for var in (self.cantidad_var, self.total_var, self.densidad_var, self.presentacion_var):
            var.trace_add("write", lambda *_, v=var: self._enforce_numeric(v))

        if self.costo_unitario_entry is not None:
            self.costo_unitario_entry.bind("<FocusIn>", lambda _event: self._strip_currency_display(self.costo_unitario_var))
            self.costo_unitario_entry.bind("<FocusOut>", lambda _event: self._format_currency(self.costo_unitario_var))

    # ── lógica de sustancias ───────────────────────────────────

    def _sustancia_codes(self) -> list[str]:
        codes = [str(item.get("codigo", "")).strip() for item in self.catalogs["sustancias"]]
        return sorted([c for c in codes if c])

    def _find_sustancia_by_code(self, code: str) -> dict | None:
        for item in self.catalogs["sustancias"]:
            if str(item.get("codigo", "")).strip() == code:
                return item
        return None

    def _on_codigo_selected(self, _event: tk.Event) -> None:
        selected = self._find_sustancia_by_code(self.codigo_var.get().strip())
        if not selected:
            self.nombre_var.set("")
            return

        self.nombre_var.set(str(selected.get("nombre", "")))
        self.codigo_contable_var.set(str(selected.get("codigo_sistema", "")))
        if not self.concentracion_var.get().strip():
            self.concentracion_var.set(str(selected.get("concentracion", "")))
        if not self.densidad_var.get().strip():
            self.densidad_var.set(str(selected.get("densidad", "")))
        if not self.unidad_var.get().strip():
            self.unidad_var.set(str(selected.get("unidad", "")))

    # ── parseo ─────────────────────────────────────────────────

    def _parse_date(self, value: str) -> date | None:
        raw = (value or "").strip()
        if not raw:
            return None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                continue
        return None

    def _to_float(self, value: str) -> float | None:
        clean = (value or "").strip().replace("$", "")
        if not clean:
            return 0.0

        if "," in clean and "." in clean:
            clean = clean.replace(",", "")
        elif "," in clean:
            clean = clean.replace(",", ".")

        clean = clean.strip()
        if not clean:
            return 0.0
        try:
            return float(clean)
        except ValueError:
            return None

    # ── recálculos ─────────────────────────────────────────────

    def _recalculate_vigencia(self) -> None:
        """Vigencia Documento = Fecha Documento + 5 años (almacenada como fecha)."""
        doc_date = self._parse_date(self.fecha_doc_var.get())
        if doc_date is None:
            self.vigencia_doc_var.set("")
            return
        try:
            vigencia = doc_date.replace(year=doc_date.year + 5)
        except ValueError:
            # Handle Feb 29 edge case
            vigencia = doc_date.replace(year=doc_date.year + 5, day=28)
        self.vigencia_doc_var.set(vigencia.strftime("%Y-%m-%d"))

    def _enforce_numeric(self, var: tk.StringVar) -> None:
        """Solo permite dígitos, punto decimal y signo negativo. Convierte comas a puntos."""
        val = var.get()
        cleaned = ""
        has_dot = False
        for ch in val:
            if ch == ",":
                ch = "."
            if ch.isdigit():
                cleaned += ch
            elif ch == "." and not has_dot:
                cleaned += ch
                has_dot = True
            elif ch == "-" and not cleaned:
                cleaned += ch
        if cleaned != val:
            var.set(cleaned)

    def _strip_currency_display(self, var: tk.StringVar) -> None:
        val = var.get().replace("$", "").replace(",", "").strip()
        if val != var.get():
            var.set(val)

    def _format_currency(self, var: tk.StringVar) -> None:
        raw = var.get().replace("$", "").replace(",", "").strip()
        if not raw:
            return

        try:
            number = float(raw)
        except ValueError:
            var.set("")
            return

        var.set(f"${number:,.2f}")

    def _recalculate_costo_total(self) -> None:
        """Costo Total = Cantidad × Costo Unitario (igual que Excel)."""
        qty = self._to_float(self.cantidad_var.get())
        cost = self._to_float(self.costo_unitario_var.get())

        if qty is None or cost is None:
            self.costo_total_var.set("")
            return

        self.costo_total_var.set(f"${round(qty * cost, 2):,.2f}")

    def _recalculate_total(self) -> None:
        """Total (contenido neto) = Cantidad × Presentación."""
        qty = self._to_float(self.cantidad_var.get())
        pres = self._to_float(self.presentacion_var.get())
        if qty is None or pres is None:
            return
        self.total_var.set(str(round(qty * pres, 2)))

    # ── acciones ───────────────────────────────────────────────

    def _load_history(self, show_all: bool = False) -> None:
        if self.history_tree is None:
            return
        self.history_tree.delete(*self.history_tree.get_children())
        records = DataHandler.get_all(ENTRADAS_FILE, "entradas")
        rows = list(reversed(records))
        if not show_all:
            rows = rows[:15]
        for rec in rows:
            anulado = rec.get("anulado", False)
            estado = "ANULADO" if anulado else "Activo"
            row = (
                rec.get("id", ""),
                rec.get("fecha", ""),
                rec.get("codigo", ""),
                rec.get("nombre", ""),
                rec.get("lote", ""),
                rec.get("total", ""),
                rec.get("unidad", ""),
                estado,
            )
            tag = "anulado" if anulado else ""
            self.history_tree.insert("", tk.END, values=row, tags=(tag,))

    def _filter_history(self) -> None:
        fecha = self.hist_fecha_var.get().strip()
        codigo = self.hist_codigo_var.get().strip()
        lote = self.hist_lote_var.get().strip()
        if not fecha and not codigo:
            self._mb_showwarning("Filtro", "Fecha y Código son obligatorios para filtrar")
            return
        if self.history_tree is None:
            return
        self.history_tree.delete(*self.history_tree.get_children())
        records = DataHandler.get_all(ENTRADAS_FILE, "entradas")
        for rec in reversed(records):
            if fecha and str(rec.get("fecha", "")).strip() != fecha:
                continue
            if codigo and str(rec.get("codigo", "")).strip() != codigo:
                continue
            if lote and str(rec.get("lote", "")).strip() != lote:
                continue
            anulado = rec.get("anulado", False)
            estado = "ANULADO" if anulado else "Activo"
            row = (
                rec.get("id", ""),
                rec.get("fecha", ""),
                rec.get("codigo", ""),
                rec.get("nombre", ""),
                rec.get("lote", ""),
                rec.get("total", ""),
                rec.get("unidad", ""),
                estado,
            )
            tag = "anulado" if anulado else ""
            self.history_tree.insert("", tk.END, values=row, tags=(tag,))

    def _clear_history_filters(self) -> None:
        """Limpia filtros del historial y muestra todo."""
        self.hist_fecha_var.set("")
        self.hist_codigo_var.set("")
        self.hist_lote_var.set("")
        self._load_history(show_all=True)

    def _edit_selected(self) -> None:
        if self.history_tree is None:
            return
        sel = self.history_tree.selection()
        if not sel:
            self._mb_showwarning("Aviso", "Selecciona un registro para editar")
            return
        values = self.history_tree.item(sel[0], "values")
        rec_id = int(values[0])

        records = DataHandler.get_all(ENTRADAS_FILE, "entradas")
        record = next((r for r in records if r.get("id") == rec_id), None)
        if not record:
            self._mb_showerror("Error", "Registro no encontrado")
            return
        if record.get("anulado", False):
            self._mb_showwarning("Aviso", "No se puede editar un registro anulado")
            return

        # Cargar datos en formulario
        self.editing_id = rec_id
        self.tipo_entrada_var.set(record.get("tipo_entrada", ""))
        self.fecha_entrada_var.set(record.get("fecha", ""))
        self.codigo_var.set(record.get("codigo", ""))
        self.nombre_var.set(record.get("nombre", ""))
        self.codigo_contable_var.set(record.get("codigo_contable", ""))
        self.lote_var.set(record.get("lote", ""))
        self.cantidad_var.set(str(record.get("cantidad", "")))
        self.presentacion_var.set(record.get("presentacion", ""))
        self.total_var.set(str(record.get("total", "")))
        self.unidad_var.set(record.get("unidad", ""))
        self.concentracion_var.set(record.get("concentracion", ""))
        self.densidad_var.set(record.get("densidad", ""))
        self.proveedor_var.set(record.get("proveedor", ""))
        self.costo_unitario_var.set(record.get("costo_unitario", ""))
        self._format_currency(self.costo_unitario_var)
        self.costo_total_var.set(record.get("costo_total", ""))
        self._format_currency(self.costo_total_var)
        self.certificado_var.set(record.get("certificado", False))
        self.msds_var.set(record.get("msds", False))
        self.fecha_venc_var.set(record.get("fecha_vencimiento", ""))
        self.fecha_doc_var.set(record.get("fecha_documento", ""))
        self.vigencia_doc_var.set(record.get("vigencia_documento", ""))
        self.ubicacion_var.set(record.get("ubicacion", ""))
        self.condicion_var.set(record.get("condicion_almacenamiento", ""))
        if self.observaciones_text is not None:
            self.observaciones_text.delete("1.0", tk.END)
            self.observaciones_text.insert("1.0", record.get("observaciones", ""))

        if self.save_btn is not None:
            self.save_btn.config(text="Actualizar")

    def _annul_selected(self) -> None:
        if self.history_tree is None:
            return
        sel = self.history_tree.selection()
        if not sel:
            self._mb_showwarning("Aviso", "Selecciona un registro para anular")
            return
        values = self.history_tree.item(sel[0], "values")
        rec_id = int(values[0])

        records = DataHandler.get_all(ENTRADAS_FILE, "entradas")
        record = next((r for r in records if r.get("id") == rec_id), None)
        if not record:
            self._mb_showerror("Error", "Registro no encontrado")
            return
        if record.get("anulado", False):
            self._mb_showwarning("Aviso", "Este registro ya está anulado")
            return

        # Verificar que anular no deje stock negativo
        codigo = str(record.get("codigo", "")).strip()
        lote = str(record.get("lote", "")).strip()
        total_rec = float(record.get("total", 0))

        salidas = DataHandler.get_all(SALIDAS_FILE, "salidas")
        entradas = DataHandler.get_all(ENTRADAS_FILE, "entradas")

        total_entrada = sum(
            float(r.get("total", 0))
            for r in entradas
            if str(r.get("codigo", "")).strip() == codigo
            and str(r.get("lote", "")).strip() == lote
            and not r.get("anulado", False)
        )
        total_salida = sum(
            float(r.get("cantidad", 0))
            for r in salidas
            if str(r.get("codigo", "")).strip() == codigo
            and str(r.get("lote", "")).strip() == lote
            and not r.get("anulado", False)
        )
        stock_after = (total_entrada - total_rec) - total_salida
        if stock_after < 0:
            self._mb_showerror(
                "Stock",
                f"No se puede anular: el stock quedaría negativo ({stock_after:.2f}).\n"
                "Primero anule las salidas correspondientes.",
            )
            return

        # Pedir motivo obligatorio
        motivo_win = tk.Toplevel(self.window)
        motivo_win.title("Motivo de anulación")
        motivo_win.geometry("420x180")
        motivo_win.configure(bg="white")
        motivo_win.transient(self.window)
        motivo_win.grab_set()

        tk.Label(motivo_win, text="Ingrese el motivo de la anulación:", bg="white",
                 font=("Segoe UI", 11)).pack(pady=(16, 6), padx=16, anchor="w")
        motivo_text = tk.Text(motivo_win, height=3, font=("Segoe UI", 10))
        motivo_text.pack(fill="x", padx=16)
        motivo_text.focus_set()

        def confirmar_anulacion():
            motivo = motivo_text.get("1.0", tk.END).strip()
            if not motivo:
                self._mb_showerror("Validación", "El motivo es obligatorio", parent=motivo_win)
                return
            DataHandler.update_record(ENTRADAS_FILE, "entradas", rec_id, {
                "anulado": True, "motivo_anulacion": motivo,
            })
            registrar_bitacora(
                usuario=self.usuario,
                tipo_operacion="Anulación",
                hoja="Entrada",
                id_registro=str(rec_id),
                campo="anulacion_entrada",
                valor_anterior=f"{codigo} | Lote: {lote} | Total: {total_rec}",
                valor_nuevo=f"ANULADO | Motivo: {motivo}",
            )
            motivo_win.destroy()
            self._mb_showinfo("Éxito", "Entrada anulada correctamente")
            sync_inventario(ENTRADAS_FILE, SALIDAS_FILE, INVENTARIO_FILE)
            self._load_history()

        tk.Button(motivo_win, text="Confirmar anulación", command=confirmar_anulacion,
                  bg=COLORS["error"], fg="white", relief="flat", padx=16, pady=6,
                  ).pack(pady=(10, 0))

    def show_label_preview(self) -> None:
        from ui.etiquetas import EtiquetasWindow
        EtiquetasWindow(self.window)

    def clear(self) -> None:
        self.editing_id = None
        if self.save_btn is not None:
            self.save_btn.config(text="Guardar")
        self.tipo_entrada_var.set("")
        self.fecha_entrada_var.set(date.today().strftime("%Y-%m-%d"))
        self.codigo_var.set("")
        self.nombre_var.set("")
        self.lote_var.set("")
        self.costo_unitario_var.set("")
        self.costo_total_var.set("$0.00")
        self.cantidad_var.set("")
        self.presentacion_var.set("")
        self.total_var.set("")
        self.unidad_var.set("")
        self.concentracion_var.set("")
        self.densidad_var.set("")
        self.proveedor_var.set("")
        self.codigo_contable_var.set("")
        self.certificado_var.set(False)
        self.msds_var.set(False)
        self.fecha_venc_var.set("")
        self.fecha_doc_var.set("")
        self.vigencia_doc_var.set("")
        self.ubicacion_var.set("")
        self.condicion_var.set("")
        if self.observaciones_text is not None:
            self.observaciones_text.delete("1.0", tk.END)

    def save(self) -> None:
        required = {
            "Tipo Entrada": self.tipo_entrada_var.get().strip(),
            "Fecha Entrada": self.fecha_entrada_var.get().strip(),
            "Codigo": self.codigo_var.get().strip(),
            "Nombre del Producto": self.nombre_var.get().strip(),
            "Cantidad": self.cantidad_var.get().strip(),
            "Total": self.total_var.get().strip(),
            "Unidad": self.unidad_var.get().strip(),
        }
        missing = [k for k, v in required.items() if not v]
        if missing:
            self._mb_showerror("Validacion", f"Completa campos obligatorios: {', '.join(missing)}")
            return

        if not self.certificado_var.get() and not self.msds_var.get():
            self._mb_showerror("Validacion", "Debe marcar al menos Certificado o MSDS")
            return

        fecha_entrada = self._parse_date(self.fecha_entrada_var.get())
        if fecha_entrada is None:
            self._mb_showerror("Validacion", "Fecha Entrada no es valida")
            return

        cantidad = self._to_float(self.cantidad_var.get())
        if cantidad is None or cantidad <= 0:
            self._mb_showerror("Validacion", "Cantidad debe ser numerica y mayor a 0")
            return

        total = self._to_float(self.total_var.get())
        if total is None or total <= 0:
            self._mb_showerror("Validacion", "Total (contenido neto) debe ser numerico y mayor a 0")
            return

        # Validar que el producto no esté vencido
        fecha_venc = self._parse_date(self.fecha_venc_var.get())
        if fecha_venc is not None and fecha_venc <= date.today():
            self._mb_showerror(
                "Producto Vencido",
                f"No se puede ingresar un producto vencido.\n"
                f"Fecha de vencimiento: {fecha_venc.strftime('%Y-%m-%d')}",
            )
            return

        observaciones = ""
        if self.observaciones_text is not None:
            observaciones = self.observaciones_text.get("1.0", tk.END).strip()

        costo_unitario_raw = self.costo_unitario_var.get().strip()
        costo_unitario = self._to_float(costo_unitario_raw)
        if costo_unitario_raw and costo_unitario is None:
            self._mb_showerror("Validacion", "Costo Unitario no es valido")
            return

        costo_total_raw = self.costo_total_var.get().strip()
        costo_total = self._to_float(costo_total_raw)
        if costo_total_raw and costo_total is None:
            self._mb_showerror("Validacion", "Costo Total no es valido")
            return

        record = {
            "tipo_entrada": self.tipo_entrada_var.get().strip(),
            "fecha": self.fecha_entrada_var.get().strip(),
            "codigo": self.codigo_var.get().strip(),
            "nombre": self.nombre_var.get().strip(),
            "codigo_contable": self.codigo_contable_var.get().strip(),
            "lote": self.lote_var.get().strip(),
            "cantidad": cantidad,
            "presentacion": self.presentacion_var.get().strip(),
            "total": total,
            "unidad": self.unidad_var.get().strip(),
            "proveedor": self.proveedor_var.get().strip(),
            "concentracion": self.concentracion_var.get().strip(),
            "densidad": self.densidad_var.get().strip(),
            "costo_unitario": "" if not costo_unitario_raw else f"{costo_unitario:.2f}",
            "costo_total": "" if not costo_total_raw else f"{costo_total:.2f}",
            "certificado": self.certificado_var.get(),
            "msds": self.msds_var.get(),
            "fecha_vencimiento": self.fecha_venc_var.get().strip(),
            "fecha_documento": self.fecha_doc_var.get().strip(),
            "vigencia_documento": self.vigencia_doc_var.get().strip(),
            "condicion_almacenamiento": self.condicion_var.get().strip(),
            "ubicacion": self.ubicacion_var.get().strip(),
            "observaciones": observaciones,
        }

        if self.editing_id is not None:
            # ── Modo edición ──
            if not self._mb_askyesno("Confirmar", "¿Desea actualizar esta entrada?"):
                return

            old_records = DataHandler.get_all(ENTRADAS_FILE, "entradas")
            old_rec = next((r for r in old_records if r.get("id") == self.editing_id), {})

            # Detectar campos cambiados para bitácora
            changes: list[tuple[str, str, str]] = []
            for field, new_val in record.items():
                old_val = old_rec.get(field, "")
                if str(new_val) != str(old_val):
                    changes.append((field, str(old_val), str(new_val)))

            if not DataHandler.update_record(ENTRADAS_FILE, "entradas", self.editing_id, record):
                self._mb_showerror("Error", "No se pudo actualizar la entrada")
                return

            for campo, anterior, nuevo in changes:
                registrar_bitacora(
                    usuario=self.usuario,
                    tipo_operacion="Edición",
                    hoja="Entrada",
                    id_registro=str(self.editing_id),
                    campo=campo,
                    valor_anterior=anterior,
                    valor_nuevo=nuevo,
                )

            self._mb_showinfo("Éxito", "Entrada actualizada correctamente")
            sync_inventario(ENTRADAS_FILE, SALIDAS_FILE, INVENTARIO_FILE)
            self.clear()
            self._load_history()
            return

        # ── Modo creación ──
        if not self._mb_askyesno("Confirmar", "¿Desea guardar esta entrada?"):
            return

        if not DataHandler.add_record(ENTRADAS_FILE, "entradas", record):
            self._mb_showerror("Error", "No se pudo guardar la entrada")
            return

        tipo_ent = self.tipo_entrada_var.get().strip() or "Entrada"
        registrar_bitacora(
            usuario=self.usuario,
            tipo_operacion="Entrada",
            hoja=tipo_ent,
            id_registro=str(record.get("id", "")),
            campo="entrada_completa",
            valor_anterior="",
            valor_nuevo=f"{record['codigo']} | Lote: {record.get('lote', '')} | Total: {record['total']}",
        )

        self._mb_showinfo("Exito", "Entrada registrada correctamente")
        sync_inventario(ENTRADAS_FILE, SALIDAS_FILE, INVENTARIO_FILE)
        self.clear()
        self._load_history()

