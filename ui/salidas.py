import tkinter as tk
from datetime import date, datetime
from tkinter import messagebox
from tkinter import ttk

from tkcalendar import DateEntry

from config.config import (
    COLORS,
    ENTRADAS_FILE,
    INVENTARIO_FILE,
    SALIDAS_FILE,
    TIPOS_SALIDA_FILE,
    UBICACIONES_FILE,
    UBICACIONES_USO_FILE,
)
from ui.bitacora import registrar_bitacora
from ui.styles import apply_styles_to_window, make_required_label, apply_focus_bindings, build_header
from utils.data_handler import DataHandler, sync_inventario


class SalidasWindow:
    """Formulario de salidas – layout alineado al Excel Kardex."""

    def __init__(self, parent: tk.Tk, usuario: str = "", rol: str = ""):
        self.window = tk.Toplevel(parent)
        self.window.title("Sistema de Gestion - Salidas")
        self.window.geometry("1280x880")
        self.window.configure(bg=COLORS["secondary"])
        self.usuario = usuario
        self.rol = rol.lower()
        self.editing_id: int | None = None

        # ── variables ──
        self.tipo_salida_var = tk.StringVar()
        self.fecha_salida_var = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        self.codigo_var = tk.StringVar()
        self.nombre_var = tk.StringVar()
        self.lote_var = tk.StringVar()
        self.ubicacion_var = tk.StringVar()

        self.vigencia_var = tk.StringVar()
        self.dias_vigencia_var = tk.StringVar()
        self.stock_actual_var = tk.StringVar(value="0")
        self.nuevo_stock_var = tk.StringVar(value="0")
        self.unidad_stock_var = tk.StringVar()

        self.cantidad_var = tk.StringVar()
        self.unidad_var = tk.StringVar()
        self.densidad_var = tk.StringVar()
        self.peso_inicial_var = tk.StringVar()
        self.peso_final_var = tk.StringVar()
        self.liquido_var = tk.BooleanVar(value=False)

        self.en_uso_var = tk.BooleanVar(value=True)

        self.tipo_combo: ttk.Combobox | None = None
        self.codigo_combo: ttk.Combobox | None = None
        self.lote_combo: ttk.Combobox | None = None
        self.ubicacion_combo: ttk.Combobox | None = None
        self.obs_text: tk.Text | None = None
        self.dias_vigencia_label: tk.Label | None = None
        self.history_tree: ttk.Treeview | None = None
        self.save_btn: tk.Button | None = None

        self._load_options()
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

    # ── datos ──────────────────────────────────────────────────

    def _load_options(self) -> None:
        tipos_data = DataHandler.load_json(TIPOS_SALIDA_FILE)
        self.tipo_salida_options = [
            x.get("nombre", "") for x in tipos_data.get("maestrasTiposSalida", []) if x.get("nombre")
        ]
        if not self.tipo_salida_options:
            self.tipo_salida_options = ["Consumo", "Transferencia", "Ajuste", "Merma"]

        ubicaciones_data = DataHandler.load_json(UBICACIONES_FILE)
        ubicaciones_uso_data = DataHandler.load_json(UBICACIONES_USO_FILE)
        self.ubicacion_options = [
            x.get("nombre", "") for x in ubicaciones_data.get("maestrasUbicaciones", []) if x.get("nombre")
        ] + [
            x.get("nombre", "") for x in ubicaciones_uso_data.get("maestrasUbicacionesUso", []) if x.get("nombre")
        ]

    def _get_entradas(self) -> list[dict]:
        return DataHandler.get_all(ENTRADAS_FILE, "entradas")

    def _get_salidas(self) -> list[dict]:
        return DataHandler.get_all(SALIDAS_FILE, "salidas")

    def _safe_float(self, value) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _calculate_stock(self, codigo: str, lote: str) -> float:
        """Stock = Sum(Entradas.Total) - Sum(Salidas.Cantidad) por (codigo, lote), excluyendo anulados."""
        entradas = self._get_entradas()
        salidas = self._get_salidas()

        total_entrada = sum(
            self._safe_float(r.get("total", 0))
            for r in entradas
            if not r.get("anulado")
            and str(r.get("codigo", "")).strip() == codigo
            and str(r.get("lote", "")).strip() == lote
        )
        total_salida = sum(
            self._safe_float(r.get("cantidad", 0))
            for r in salidas
            if not r.get("anulado")
            and str(r.get("codigo", "")).strip() == codigo
            and str(r.get("lote", "")).strip() == lote
        )
        return round(total_entrada - total_salida, 6)

    def _available_codes(self) -> list[str]:
        entradas = self._get_entradas()
        codes = {str(r.get("codigo", "")).strip() for r in entradas if str(r.get("codigo", "")).strip()}
        return sorted(codes)

    def _lotes_for_code(self, code: str) -> list[str]:
        entradas = self._get_entradas()
        lotes = {
            str(r.get("lote", "")).strip()
            for r in entradas
            if str(r.get("codigo", "")).strip() == code and str(r.get("lote", "")).strip()
        }
        # Filtrar lotes sin stock disponible
        return sorted(l for l in lotes if self._calculate_stock(code, l) > 0)

    def _first_entrada_for(self, codigo: str, lote: str = "") -> dict | None:
        for r in self._get_entradas():
            if str(r.get("codigo", "")).strip() != codigo:
                continue
            if lote and str(r.get("lote", "")).strip() != lote:
                continue
            return r
        return None

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

        build_header(wrapper, "Sistema de Gestión  -  Salidas")

        # ── Información General ──
        general = tk.LabelFrame(wrapper, text="Información General", bg="white", fg="#1F4F8A", font=("Segoe UI", 11, "bold"))
        general.pack(fill="x", padx=4, pady=(0, 8))

        row1 = tk.Frame(general, bg="white")
        row1.pack(fill="x", padx=10, pady=8)

        self.tipo_combo = self._add_combo(row1, "Tipo Salida", self.tipo_salida_var, self.tipo_salida_options, 0, required=True)
        self._add_date_entry(row1, "Fecha Salida", self.fecha_salida_var, 1, required=True)
        self.codigo_combo = self._add_combo(row1, "Codigo", self.codigo_var, self._available_codes(), 2, required=True)
        self._add_entry(row1, "Nombre del Producto", self.nombre_var, 3, readonly=True)
        self.lote_combo = self._add_combo(row1, "Lote", self.lote_var, [], 4, required=True)
        self.ubicacion_combo = self._add_combo(row1, "Ubicación Origen", self.ubicacion_var, self.ubicacion_options, 5)

        # ── Vigencia y Stock ──
        vig_stock = tk.LabelFrame(wrapper, text="Vigencia y Stock", bg="white", fg="#1F4F8A", font=("Segoe UI", 11, "bold"))
        vig_stock.pack(fill="x", padx=4, pady=(0, 8))

        row2 = tk.Frame(vig_stock, bg="white")
        row2.pack(fill="x", padx=10, pady=8)

        # Vigencia (fecha vencimiento, readonly)
        self._add_entry(row2, "Vigencia", self.vigencia_var, 0, readonly=True)

        # Días Vigencia (label con color dinámico)
        dias_frame = tk.Frame(row2, bg="white")
        dias_frame.grid(row=0, column=1, padx=8, sticky="ew")
        tk.Label(dias_frame, text="Días Vigencia", bg="white").pack(anchor="w")
        self.dias_vigencia_label = tk.Label(
            dias_frame, text="", bg="white", font=("Segoe UI", 10, "bold"),
            anchor="w", padx=6, pady=4, relief="solid", bd=1,
        )
        self.dias_vigencia_label.pack(fill="x", pady=(4, 0))
        row2.columnconfigure(1, weight=1)

        self._add_entry(row2, "Stock", self.stock_actual_var, 2, readonly=True)
        self._add_entry(row2, "Nueva Stock", self.nuevo_stock_var, 3, readonly=True)
        self._add_entry(row2, "Unidad", self.unidad_stock_var, 4, readonly=True)

        # ── Detalles del Producto ──
        detalles = tk.LabelFrame(wrapper, text="Detalles del Producto", bg="white", fg="#1F4F8A", font=("Segoe UI", 11, "bold"))
        detalles.pack(fill="x", padx=4, pady=(0, 8))

        row3 = tk.Frame(detalles, bg="white")
        row3.pack(fill="x", padx=10, pady=8)

        self._add_entry(row3, "Cantidad", self.cantidad_var, 0, required=True)
        self._add_entry(row3, "Unidad", self.unidad_var, 1, readonly=True)
        self._add_entry(row3, "Densidad (g/mL)", self.densidad_var, 2, readonly=True)
        self._add_entry(row3, "Peso Inicial", self.peso_inicial_var, 3)
        self._add_entry(row3, "Peso Final", self.peso_final_var, 4)

        chk_frame = tk.Frame(row3, bg="white")
        chk_frame.grid(row=0, column=5, padx=8, sticky="ew")
        tk.Label(chk_frame, text=" ", bg="white").pack(anchor="w")
        tk.Checkbutton(chk_frame, text="Líquido", variable=self.liquido_var, bg="white", font=("Segoe UI", 10)).pack(anchor="w", pady=(6, 0))
        row3.columnconfigure(5, weight=0)

        # ── Observaciones de Salida ──
        obs = tk.LabelFrame(wrapper, text="Observaciones de Salida", bg="white", fg="#1F4F8A", font=("Segoe UI", 11, "bold"))
        obs.pack(fill="x", padx=4, pady=(0, 8))

        row4 = tk.Frame(obs, bg="white")
        row4.pack(fill="x", padx=10, pady=8)

        obs_left = tk.Frame(row4, bg="white")
        obs_left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        tk.Label(obs_left, text="Observaciones", bg="white").pack(anchor="w")
        self.obs_text = tk.Text(obs_left, height=3)
        self.obs_text.pack(fill="x", pady=(4, 0))

        obs_right = tk.Frame(row4, bg="white")
        obs_right.pack(side="right", padx=(10, 0), anchor="se")
        tk.Checkbutton(obs_right, text="EN USO", variable=self.en_uso_var, bg="white", font=("Segoe UI", 10, "bold")).pack(anchor="e", pady=(10, 0))

        # ── Botones ──
        actions = tk.Frame(wrapper, bg="white")
        actions.pack(fill="x", pady=(6, 0))

        self.save_btn = tk.Button(
            actions, text="Guardar", command=self.save,
            bg=COLORS["primary"], fg=COLORS["text_light"], relief="flat",
            font=("Segoe UI", 11, "bold"), padx=28, pady=7,
        )
        self.save_btn.pack(side="left", expand=True, padx=6)
        tk.Button(
            actions, text="Salir", command=self.window.destroy,
            bg=COLORS["primary"], fg=COLORS["text_light"], relief="flat",
            font=("Segoe UI", 11, "bold"), padx=28, pady=7,
        ).pack(side="left", expand=True, padx=6)

        # ── Historial ──
        hist_frame = tk.LabelFrame(wrapper, text="Historial de Salidas", bg="white", fg="#1F4F8A", font=("Segoe UI", 11, "bold"))
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

        hist_cols = ("id", "fecha", "tipo", "codigo", "nombre", "lote", "cantidad", "estado")
        tree_container = tk.Frame(hist_frame, bg="white")
        tree_container.pack(fill="both", expand=True, padx=6, pady=(2, 4))

        self.history_tree = ttk.Treeview(tree_container, columns=hist_cols, show="headings", height=5)
        hist_scroll_y = ttk.Scrollbar(tree_container, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=hist_scroll_y.set)
        self.history_tree.pack(side="left", fill="both", expand=True)
        hist_scroll_y.pack(side="right", fill="y")

        for col, heading, width in [
            ("id", "ID", 40), ("fecha", "Fecha", 90), ("tipo", "Tipo", 90),
            ("codigo", "Código", 80), ("nombre", "Nombre", 180), ("lote", "Lote", 100),
            ("cantidad", "Cantidad", 80), ("estado", "Estado", 90),
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
        col: int, required: bool = False,
    ) -> DateEntry:
        frame = tk.Frame(parent, bg="white")
        frame.grid(row=0, column=col, padx=8, sticky="ew")
        if required:
            make_required_label(frame, label).pack(anchor="w")
        else:
            tk.Label(frame, text=label, bg="white").pack(anchor="w")
        de = DateEntry(
            frame, textvariable=variable, date_pattern="yyyy-mm-dd",
            width=14, background=COLORS["primary"], foreground="white",
            headersbackground=COLORS["primary"], headersforeground="white",
        )
        de.pack(fill="x", pady=(4, 0))
        if not variable.get().strip():
            de.delete(0, tk.END)
        parent.columnconfigure(col, weight=1)
        return de

    def _add_entry(
        self, parent: tk.Widget, label: str, variable: tk.StringVar,
        col: int, readonly: bool = False, required: bool = False,
    ) -> tk.Entry:
        frame = tk.Frame(parent, bg="white")
        frame.grid(row=0, column=col, padx=8, sticky="ew")
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
        options: list[str], col: int, required: bool = False,
    ) -> ttk.Combobox:
        frame = tk.Frame(parent, bg="white")
        frame.grid(row=0, column=col, padx=8, sticky="ew")
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
        self.cantidad_var.trace_add("write", lambda *_: self._recalculate_new_stock())
        if self.codigo_combo is not None:
            self.codigo_combo.bind("<<ComboboxSelected>>", self._on_code_selected)
        if self.lote_combo is not None:
            self.lote_combo.bind("<<ComboboxSelected>>", self._on_lote_selected)

        # Validación numérica (solo dígitos, punto, signo negativo; comas → puntos)
        for var in (self.cantidad_var, self.densidad_var, self.peso_inicial_var, self.peso_final_var):
            var.trace_add("write", lambda *_, v=var: self._enforce_numeric(v))

        # Auto-cálculo cantidad por peso
        for var in (self.peso_inicial_var, self.peso_final_var, self.densidad_var):
            var.trace_add("write", lambda *_: self._calculate_qty_from_weight())
        self.liquido_var.trace_add("write", lambda *_: self._calculate_qty_from_weight())

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

    def _on_code_selected(self, _event: tk.Event) -> None:
        code = self.codigo_var.get().strip()
        if not code:
            return

        rec = self._first_entrada_for(code)
        self.nombre_var.set(str(rec.get("nombre", "")) if rec else "")

        lotes = self._lotes_for_code(code)
        if self.lote_combo is not None:
            self.lote_combo["values"] = lotes

        if lotes:
            self.lote_var.set(lotes[0])
            self._on_lote_selected(None)
        else:
            self._update_stock_display(code, "")

    def _on_lote_selected(self, _event: tk.Event | None) -> None:
        code = self.codigo_var.get().strip()
        lote = self.lote_var.get().strip()
        self._update_stock_display(code, lote)

    def _update_stock_display(self, codigo: str, lote: str) -> None:
        stock = self._calculate_stock(codigo, lote)
        self.stock_actual_var.set(f"{stock:,.2f}")

        rec = self._first_entrada_for(codigo, lote)
        if rec:
            unit = str(rec.get("unidad", ""))
            self.unidad_stock_var.set(unit)
            self.unidad_var.set(unit)
            self.densidad_var.set(str(rec.get("densidad", "")))
            self.ubicacion_var.set(str(rec.get("ubicacion", "")))

            # Vigencia
            fv = str(rec.get("fecha_vencimiento", "")).strip()
            self.vigencia_var.set(fv)
            self._update_dias_vigencia(fv)

        self._recalculate_new_stock()

    def _update_dias_vigencia(self, fecha_vencimiento: str) -> None:
        if self.dias_vigencia_label is None:
            return

        fv_date = self._parse_date(fecha_vencimiento)
        if fv_date is None:
            self.dias_vigencia_label.config(text="", bg="white")
            return

        dias = (fv_date - date.today()).days

        if dias <= 0:
            texto = f"VENCIDO ({abs(dias)} días)"
            color_bg = "#F44336"
            color_fg = "white"
        elif dias <= 30:
            texto = f"Proximo a Vencer {dias} días"
            color_bg = "#FFD600"
            color_fg = "#333333"
        else:
            texto = f"VIGENTE ({dias} días)"
            color_bg = "#4CAF50"
            color_fg = "white"

        self.dias_vigencia_label.config(text=texto, bg=color_bg, fg=color_fg)

    def _recalculate_new_stock(self) -> None:
        stock_str = self.stock_actual_var.get().strip().replace(",", "")
        try:
            stock = float(stock_str)
        except (TypeError, ValueError):
            stock = 0.0

        qty_str = self.cantidad_var.get().strip().replace(",", ".")
        if not qty_str:
            self.nuevo_stock_var.set(f"{stock:,.2f}")
            return

        try:
            qty = float(qty_str)
        except ValueError:
            self.nuevo_stock_var.set("-")
            return

        self.nuevo_stock_var.set(f"{round(stock - qty, 6):,.2f}")

    def _calculate_qty_from_weight(self) -> None:
        """Calcula cantidad = (pesoInicial - pesoFinal) [/ densidad si es líquido]."""
        pi_str = self.peso_inicial_var.get().strip().replace(",", ".")
        pf_str = self.peso_final_var.get().strip().replace(",", ".")

        if not pi_str or not pf_str:
            return

        try:
            pi = float(pi_str)
            pf = float(pf_str)
        except ValueError:
            self.cantidad_var.set("")
            return

        diff = pi - pf

        if self.liquido_var.get():
            d_str = self.densidad_var.get().strip().replace(",", ".")
            try:
                densidad = float(d_str)
            except (ValueError, TypeError):
                densidad = 0.0
            if densidad == 0:
                self.cantidad_var.set("")
                return
            result = diff / densidad
        else:
            result = diff

        # Redondear al máximo de decimales de los valores de entrada
        dec_pi = len(pi_str.split(".")[-1]) if "." in pi_str else 0
        dec_pf = len(pf_str.split(".")[-1]) if "." in pf_str else 0
        decimals = max(dec_pi, dec_pf)
        self.cantidad_var.set(str(round(result, decimals)))

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
        clean = (value or "").strip().replace(",", "")
        if not clean:
            return 0.0
        try:
            return float(clean)
        except ValueError:
            return None

    # ── historial y edición ───────────────────────────────────

    def _load_history(self, show_all: bool = False) -> None:
        if self.history_tree is None:
            return
        self.history_tree.delete(*self.history_tree.get_children())
        records = DataHandler.get_all(SALIDAS_FILE, "salidas")
        rows = list(reversed(records))
        if not show_all:
            rows = rows[:15]
        for rec in rows:
            anulado = rec.get("anulado", False)
            estado = "ANULADO" if anulado else "Activo"
            row = (
                rec.get("id", ""),
                rec.get("fecha_salida", ""),
                rec.get("tipo_salida", ""),
                rec.get("codigo", ""),
                rec.get("nombre", ""),
                rec.get("lote", ""),
                rec.get("cantidad", ""),
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
        records = DataHandler.get_all(SALIDAS_FILE, "salidas")
        for rec in reversed(records):
            if fecha and str(rec.get("fecha_salida", "")).strip() != fecha:
                continue
            if codigo and str(rec.get("codigo", "")).strip() != codigo:
                continue
            if lote and str(rec.get("lote", "")).strip() != lote:
                continue
            anulado = rec.get("anulado", False)
            estado = "ANULADO" if anulado else "Activo"
            row = (
                rec.get("id", ""),
                rec.get("fecha_salida", ""),
                rec.get("tipo_salida", ""),
                rec.get("codigo", ""),
                rec.get("nombre", ""),
                rec.get("lote", ""),
                rec.get("cantidad", ""),
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

        records = DataHandler.get_all(SALIDAS_FILE, "salidas")
        record = next((r for r in records if r.get("id") == rec_id), None)
        if not record:
            self._mb_showerror("Error", "Registro no encontrado")
            return
        if record.get("anulado", False):
            self._mb_showwarning("Aviso", "No se puede editar un registro anulado")
            return

        self.editing_id = rec_id
        self.tipo_salida_var.set(record.get("tipo_salida", ""))
        self.fecha_salida_var.set(record.get("fecha_salida", ""))
        self.codigo_var.set(record.get("codigo", ""))
        self.nombre_var.set(record.get("nombre", ""))
        self.lote_var.set(record.get("lote", ""))
        self.ubicacion_var.set(record.get("ubicacion_origen", ""))
        self.cantidad_var.set(str(record.get("cantidad", "")))
        self.unidad_var.set(record.get("unidad", ""))
        self.densidad_var.set(record.get("densidad", ""))
        self.peso_inicial_var.set(record.get("peso_inicial", ""))
        self.peso_final_var.set(record.get("peso_final", ""))
        self.liquido_var.set(record.get("liquido", False))
        self.en_uso_var.set(record.get("en_uso", True))
        if self.obs_text is not None:
            self.obs_text.delete("1.0", tk.END)
            self.obs_text.insert("1.0", record.get("observaciones", ""))

        # Actualizar stock display
        code = record.get("codigo", "")
        lote = record.get("lote", "")
        if code and lote:
            self._update_stock_display(code, lote)

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

        records = DataHandler.get_all(SALIDAS_FILE, "salidas")
        record = next((r for r in records if r.get("id") == rec_id), None)
        if not record:
            self._mb_showerror("Error", "Registro no encontrado")
            return
        if record.get("anulado", False):
            self._mb_showwarning("Aviso", "Este registro ya está anulado")
            return

        codigo = str(record.get("codigo", "")).strip()
        lote = str(record.get("lote", "")).strip()
        cantidad = float(record.get("cantidad", 0))

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
            DataHandler.update_record(SALIDAS_FILE, "salidas", rec_id, {
                "anulado": True, "motivo_anulacion": motivo,
            })
            registrar_bitacora(
                usuario=self.usuario,
                tipo_operacion="Anulación",
                hoja="Salida",
                id_registro=str(rec_id),
                campo="anulacion_salida",
                valor_anterior=f"{codigo} | Lote: {lote} | Cant: {cantidad}",
                valor_nuevo=f"ANULADO | Motivo: {motivo}",
            )
            motivo_win.destroy()
            self._mb_showinfo("Éxito", "Salida anulada correctamente")
            sync_inventario(ENTRADAS_FILE, SALIDAS_FILE, INVENTARIO_FILE)
            self._load_history()

        tk.Button(motivo_win, text="Confirmar anulación", command=confirmar_anulacion,
                  bg=COLORS["error"], fg="white", relief="flat", padx=16, pady=6,
                  ).pack(pady=(10, 0))

    # ── guardar ────────────────────────────────────────────────

    def save(self) -> None:
        required = {
            "Tipo Salida": self.tipo_salida_var.get().strip(),
            "Fecha Salida": self.fecha_salida_var.get().strip(),
            "Codigo": self.codigo_var.get().strip(),
            "Lote": self.lote_var.get().strip(),
            "Cantidad": self.cantidad_var.get().strip(),
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            self._mb_showerror("Validacion", f"Completa campos obligatorios: {', '.join(missing)}")
            return

        salida_date = self._parse_date(self.fecha_salida_var.get())
        if salida_date is None:
            self._mb_showerror("Validacion", "Fecha Salida no es valida")
            return

        cantidad = self._to_float(self.cantidad_var.get())
        if cantidad is None or cantidad <= 0:
            self._mb_showerror("Validacion", "Cantidad debe ser numerica y mayor a 0")
            return

        codigo = self.codigo_var.get().strip()
        lote = self.lote_var.get().strip()
        current_stock = self._calculate_stock(codigo, lote)

        if cantidad > current_stock:
            self._mb_showerror("Stock", "La cantidad de salida no puede superar el stock disponible")
            return

        observaciones = ""
        if self.obs_text is not None:
            observaciones = self.obs_text.get("1.0", tk.END).strip()

        salida_record = {
            "fecha_salida": self.fecha_salida_var.get().strip(),
            "tipo_salida": self.tipo_salida_var.get().strip(),
            "codigo": codigo,
            "nombre": self.nombre_var.get().strip(),
            "lote": lote,
            "cantidad": cantidad,
            "unidad": self.unidad_var.get().strip() or self.unidad_stock_var.get().strip(),
            "densidad": self.densidad_var.get().strip(),
            "ubicacion_origen": self.ubicacion_var.get().strip(),
            "peso_inicial": self.peso_inicial_var.get().strip(),
            "peso_final": self.peso_final_var.get().strip(),
            "liquido": self.liquido_var.get(),
            "en_uso": self.en_uso_var.get(),
            "observaciones": observaciones,
        }

        # ── Modo edición ──
        if self.editing_id is not None:
            if not self._mb_askyesno("Confirmar", "¿Desea actualizar esta salida?"):
                return
            records = DataHandler.get_all(SALIDAS_FILE, "salidas")
            old = next((r for r in records if r.get("id") == self.editing_id), {})
            changes: dict[str, tuple[str, str]] = {}
            for key, new_val in salida_record.items():
                old_val = old.get(key, "")
                if str(old_val) != str(new_val):
                    changes[key] = (str(old_val), str(new_val))
            DataHandler.update_record(SALIDAS_FILE, "salidas", self.editing_id, salida_record)
            for campo, (ant, nue) in changes.items():
                registrar_bitacora(
                    usuario=self.usuario,
                    tipo_operacion="Edición",
                    hoja="Salida",
                    id_registro=str(self.editing_id),
                    campo=campo,
                    valor_anterior=ant,
                    valor_nuevo=nue,
                )
            self._mb_showinfo("Éxito", "Salida actualizada correctamente")
            sync_inventario(ENTRADAS_FILE, SALIDAS_FILE, INVENTARIO_FILE)
            self._reset_form()
            self._load_history()
            return

        # ── Modo creación ──
        if not self._mb_askyesno("Confirmar", "¿Desea registrar esta salida?"):
            return

        if not DataHandler.add_record(SALIDAS_FILE, "salidas", salida_record):
            self._mb_showerror("Error", "No se pudo registrar la salida")
            return

        tipo_sal = self.tipo_salida_var.get().strip() or "Salida"
        registrar_bitacora(
            usuario=self.usuario,
            tipo_operacion="Salida",
            hoja=tipo_sal,
            id_registro=str(salida_record.get("id", "")),
            campo="salida_completa",
            valor_anterior="",
            valor_nuevo=f"{codigo} | Lote: {lote} | Cant: {cantidad}",
        )

        self._mb_showinfo("Exito", "Salida registrada correctamente")
        sync_inventario(ENTRADAS_FILE, SALIDAS_FILE, INVENTARIO_FILE)
        self._reset_form()
        self._load_history()

    def _reset_form(self) -> None:
        self.editing_id = None
        if self.save_btn is not None:
            self.save_btn.config(text="Guardar")
        self.tipo_salida_var.set("")
        self.fecha_salida_var.set(date.today().strftime("%Y-%m-%d"))
        self.codigo_var.set("")
        self.nombre_var.set("")
        self.lote_var.set("")
        self.ubicacion_var.set("")

        self.vigencia_var.set("")
        self.dias_vigencia_var.set("")
        if self.dias_vigencia_label is not None:
            self.dias_vigencia_label.config(text="", bg="white")
        self.stock_actual_var.set("0")
        self.nuevo_stock_var.set("0")
        self.unidad_stock_var.set("")

        self.cantidad_var.set("")
        self.unidad_var.set("")
        self.densidad_var.set("")
        self.peso_inicial_var.set("")
        self.peso_final_var.set("")
        self.liquido_var.set(False)

        self.en_uso_var.set(True)

        if self.obs_text is not None:
            self.obs_text.delete("1.0", tk.END)

        if self.codigo_combo is not None:
            self.codigo_combo["values"] = self._available_codes()
        if self.lote_combo is not None:
            self.lote_combo["values"] = []
        if self.tipo_combo is not None:
            self.tipo_combo["values"] = self.tipo_salida_options

