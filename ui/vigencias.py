import tkinter as tk
from datetime import date, datetime
from tkinter import messagebox, ttk

from config.config import (
    COLORS,
    ENTRADAS_FILE,
    INVENTARIO_FILE,
    PROVEEDORES_FILE,
    SALIDAS_FILE,
    SUSTANCIAS_FILE,
    TIPOS_SALIDA_FILE,
    UBICACIONES_FILE,
    UBICACIONES_USO_FILE,
    UNIDADES_FILE,
)
from ui.bitacora import registrar_bitacora
from ui.styles import build_header
from utils.data_handler import (
    DataHandler,
    Lookups,
    build_location_indexes,
    build_substance_indexes,
    location_name,
    substance_code,
    substance_name,
    sync_inventario,
)


class VigenciasWindow:
    """Vista de vigencias de inventario con dias restantes y estado."""

    def __init__(self, parent: tk.Tk, usuario: str = "", rol: str = ""):
        self.window = tk.Toplevel(parent)
        self.window.title("Sistema de Gestion - Vigencias")
        self.window.geometry("1200x650")
        self.window.configure(bg=COLORS["secondary"])
        self.usuario = usuario
        self.rol = rol.lower()

        self.search_var = tk.StringVar()
        self.tree: ttk.Treeview | None = None
        self._tree_columns: tuple[str, ...] = ()
        self._tree_base_widths: dict[str, int] = {}
        self.estado_label: tk.Label | None = None
        self.row_records: dict[str, dict] = {}
        self.pagina_actual = 1
        self.total_paginas = 1
        self.por_pagina_var = tk.StringVar(value="50")
        self.pag_label: tk.Label | None = None
        self.sort_mode = "default"

        self.detail_vars = {
            "codigo": tk.StringVar(),
            "nombre": tk.StringVar(),
            "lote": tk.StringVar(),
            "fecha_vencimiento": tk.StringVar(),
            "dias_restantes": tk.StringVar(),
            "estado": tk.StringVar(),
            "cantidad": tk.StringVar(),
            "unidad": tk.StringVar(),
            "fabricante": tk.StringVar(),
        }

        # Variables para Mover Stock
        self.tipo_salida_var = tk.StringVar()
        self.obs_text: tk.Text | None = None

        tipos_data = DataHandler.load_json(TIPOS_SALIDA_FILE)
        self.tipo_salida_options = [
            x.get("nombre", "") for x in tipos_data.get("maestrasTiposSalida", []) if x.get("nombre")
        ]
        if not self.tipo_salida_options:
            self.tipo_salida_options = ["Consumo", "Transferencia", "Ajuste", "Merma"]

        tipos_salida_cat = tipos_data.get("maestrasTiposSalida", [])
        unidades_cat = DataHandler.load_json(UNIDADES_FILE).get("maestrasUnidades", [])
        proveedores_cat = DataHandler.load_json(PROVEEDORES_FILE).get("maestrasProveedores", [])
        sustancias_cat = DataHandler.load_json(SUSTANCIAS_FILE).get("maestrasSustancias", [])
        ubicaciones_cat = DataHandler.load_json(UBICACIONES_FILE).get("maestrasUbicaciones", [])
        ubicaciones_uso_cat = DataHandler.load_json(UBICACIONES_USO_FILE).get("maestrasUbicacionesUso", [])
        self.lkp = Lookups(
            tipos_salida=tipos_salida_cat,
            unidades=unidades_cat,
            proveedores=proveedores_cat,
        )
        self.sustancias_by_id, _ = build_substance_indexes(sustancias_cat)
        self.locations_by_key, _ = build_location_indexes(ubicaciones_cat, ubicaciones_uso_cat)

        self._build_ui()
        self.window.bind("<Escape>", lambda _e: self.window.destroy())
        self.load_table()

    def _build_ui(self) -> None:
        outer = tk.Frame(self.window, bg="white", bd=1, relief="solid")
        outer.pack(expand=True, fill="both", padx=14, pady=14)

        self._canvas = tk.Canvas(outer, bg="white", highlightthickness=0)
        v_scroll = ttk.Scrollbar(outer, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=v_scroll.set)
        v_scroll.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        wrapper = tk.Frame(self._canvas, bg="white", padx=12, pady=12)
        self._canvas_window = self._canvas.create_window((0, 0), window=wrapper, anchor="nw")
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        wrapper.bind("<Configure>", lambda _e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas.bind(
            "<Configure>",
            lambda e: (
                self._canvas.itemconfigure(self._canvas_window, width=e.width),
                self._canvas.configure(scrollregion=self._canvas.bbox("all")),
            ),
        )
        self._canvas.bind("<Enter>", lambda _e: self._canvas.bind_all("<MouseWheel>", self._on_mousewheel))
        self._canvas.bind("<Leave>", lambda _e: self._canvas.unbind_all("<MouseWheel>"))

        build_header(wrapper, "Sistema de Gestión  -  Vigencias")

        search_row = tk.Frame(wrapper, bg="white")
        search_row.pack(fill="x", pady=(0, 8))

        tk.Entry(search_row, textvariable=self.search_var).pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Button(
            search_row,
            text="Buscar",
            command=self.load_table,
            bg=COLORS["primary"],
            fg=COLORS["text_light"],
            relief="flat",
            padx=16,
            pady=5,
        ).pack(side="left", padx=(0, 8))
        tk.Button(
            search_row,
            text="⟳ Refrescar",
            command=self.load_table,
            bg=COLORS["border"],
            fg=COLORS["text_dark"],
            relief="flat",
            padx=10,
            pady=5,
        ).pack(side="left", padx=(0, 8))
        tk.Button(
            search_row,
            text="Dias Restantes de Vigencia",
            command=self.sort_by_days,
            bg=COLORS["border"],
            fg=COLORS["text_dark"],
            relief="flat",
            padx=10,
            pady=5,
        ).pack(side="left", padx=(0, 8))
        tk.Button(
            search_row,
            text="Vigencia Documento",
            command=self.sort_by_date,
            bg=COLORS["border"],
            fg=COLORS["text_dark"],
            relief="flat",
            padx=10,
            pady=5,
        ).pack(side="left")

        columns = ("codigo", "nombre", "lote", "f_venc", "cantidad", "unidad", "proveedor", "dias", "estado")
        self._tree_columns = columns
        self.tree = ttk.Treeview(wrapper, columns=columns, show="headings", height=12, selectmode="extended")
        self.tree.pack(expand=True, fill="both", pady=(0, 10))
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        style = ttk.Style(self.window)
        style.configure("Treeview", background="white", foreground="black", rowheight=25, fieldbackground="white")
        style.map("Treeview", background=[("selected", COLORS["primary"])], foreground=[("selected", "white")])

        headings = {
            "codigo": "Codigo",
            "nombre": "Nombre",
            "lote": "Lote",
            "f_venc": "F. Vencimiento",
            "cantidad": "Cantidad",
            "unidad": "Unidad",
            "proveedor": "Proveedor",
            "dias": "Dias Restantes",
            "estado": "Estado",
        }
        widths = {
            "codigo": 85,
            "nombre": 280,
            "lote": 120,
            "f_venc": 120,
            "cantidad": 90,
            "unidad": 80,
            "proveedor": 180,
            "dias": 120,
            "estado": 120,
        }

        for col in columns:
            self.tree.heading(col, text=headings[col], command=lambda c=col: self._sort_column(c, False))
            self.tree.column(col, width=widths[col], minwidth=max(60, int(widths[col] * 0.5)), anchor="w", stretch=True)
        self._tree_base_widths = widths
        self.tree.bind("<Configure>", self._on_tree_resize, add="+")

        pag_frame = tk.Frame(wrapper, bg="white")
        pag_frame.pack(fill="x", padx=2, pady=(6, 2))
        tk.Button(
            pag_frame, text="◄ Primera", command=lambda: self._ir_pagina(1),
            bg=COLORS["border"], fg=COLORS["text_dark"], relief="flat", padx=8, pady=3,
        ).pack(side="left", padx=(0, 4))
        tk.Button(
            pag_frame, text="Anterior", command=lambda: self._ir_pagina(self.pagina_actual - 1),
            bg=COLORS["border"], fg=COLORS["text_dark"], relief="flat", padx=8, pady=3,
        ).pack(side="left", padx=(0, 4))

        self.pag_label = tk.Label(pag_frame, text="Página 1 de 1", bg="white", font=("Segoe UI", 9))
        self.pag_label.pack(side="left", padx=10)

        tk.Button(
            pag_frame, text="Siguiente", command=lambda: self._ir_pagina(self.pagina_actual + 1),
            bg=COLORS["border"], fg=COLORS["text_dark"], relief="flat", padx=8, pady=3,
        ).pack(side="left", padx=(0, 4))
        tk.Button(
            pag_frame, text="Última ►", command=lambda: self._ir_pagina(self.total_paginas),
            bg=COLORS["border"], fg=COLORS["text_dark"], relief="flat", padx=8, pady=3,
        ).pack(side="left")

        tk.Label(pag_frame, text="Mostrar:", bg="white").pack(side="left", padx=(15, 4))
        por_pagina_combo = ttk.Combobox(
            pag_frame,
            textvariable=self.por_pagina_var,
            values=["20", "50", "100", "200"],
            state="readonly",
            width=6,
        )
        por_pagina_combo.pack(side="left", padx=(0, 4))
        por_pagina_combo.bind("<<ComboboxSelected>>", lambda _e: self._cambiar_por_pagina())

        details = tk.Frame(wrapper, bg="white")
        details.pack(fill="x")

        fields = [
            ("Codigo", "codigo"),
            ("Nombre del Producto", "nombre"),
            ("Lote", "lote"),
            ("Fecha Vencimiento", "fecha_vencimiento"),
            ("Dias Restantes", "dias_restantes"),
            ("Estado", "estado"),
            ("Cantidad", "cantidad"),
            ("Unidad", "unidad"),
            ("Proveedor", "fabricante"),
        ]

        for idx, (label, key) in enumerate(fields):
            row = idx // 3
            col = idx % 3
            group = tk.Frame(details, bg="white")
            group.grid(row=row * 2, column=col, sticky="ew", padx=8, pady=(3, 2))
            tk.Label(group, text=label, bg="white", fg=COLORS["text_dark"], anchor="w").pack(anchor="w")
            if key == "estado":
                self.estado_label = tk.Label(
                    group, text="", font=("Segoe UI", 11, "bold"),
                    bg="white", fg="#333", anchor="center", pady=2, relief="groove",
                )
                self.estado_label.pack(fill="x")
            else:
                tk.Entry(group, textvariable=self.detail_vars[key], state="readonly", font=("Segoe UI", 10)).pack(fill="x")

        for col in range(3):
            details.columnconfigure(col, weight=1)

        # ── Tipo de Salida y Observaciones ──
        salida_frame = tk.LabelFrame(wrapper, text="Tipo de Salida y Observaciones", bg="white", fg="#1F4F8A", font=("Segoe UI", 11, "bold"))
        salida_frame.pack(fill="x", pady=(6, 0))

        salida_row = tk.Frame(salida_frame, bg="white")
        salida_row.pack(fill="x", padx=10, pady=8)

        tipo_frame = tk.Frame(salida_row, bg="white")
        tipo_frame.pack(side="left", padx=(0, 12))
        tk.Label(tipo_frame, text="Tipo Salida", bg="white").pack(anchor="w")
        ttk.Combobox(
            tipo_frame, textvariable=self.tipo_salida_var,
            values=self.tipo_salida_options, state="readonly", width=18,
        ).pack(pady=(4, 0))

        obs_frame = tk.Frame(salida_row, bg="white")
        obs_frame.pack(side="left", fill="x", expand=True, padx=(0, 12))
        tk.Label(obs_frame, text="Observaciones", bg="white").pack(anchor="w")
        self.obs_text = tk.Text(obs_frame, height=2, font=("Segoe UI", 10))
        self.obs_text.pack(fill="x", pady=(4, 0))

        btn_col = tk.Frame(salida_row, bg="white")
        btn_col.pack(side="right", padx=(0, 0))

        tk.Button(
            btn_col, text="Mover Stock", command=self._mover_stock,
            bg="#4CAF50", fg="white", relief="flat",
            font=("Segoe UI", 11, "bold"), padx=18, pady=6,
        ).pack(pady=(0, 4))

        button_row = tk.Frame(wrapper, bg="white")
        button_row.pack(side="bottom", fill="x", pady=(10, 0))

        right_actions = tk.Frame(button_row, bg="white")
        right_actions.pack(side="right")

        tk.Button(
            right_actions,
            text="Quitar Lista",
            command=self.remove_selected,
            bg=COLORS["primary"],
            fg=COLORS["text_light"],
            relief="flat",
            padx=18,
            pady=6,
        ).pack(side="left", padx=(0, 8))
        tk.Button(
            right_actions,
            text="Limpiar",
            command=self.clear,
            bg=COLORS["primary"],
            fg=COLORS["text_light"],
            relief="flat",
            padx=18,
            pady=6,
        ).pack(side="left", padx=(0, 8))
        tk.Button(
            right_actions,
            text="Salir",
            command=self.window.destroy,
            bg=COLORS["primary"],
            fg=COLORS["text_light"],
            relief="flat",
            padx=18,
            pady=6,
        ).pack(side="left")

    def _on_mousewheel(self, event) -> None:
        try:
            if self._canvas.winfo_exists():
                self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except tk.TclError:
            pass

    def _on_tree_resize(self, event: tk.Event) -> None:
        if self.tree is None or not self._tree_columns:
            return
        total_base = sum(self._tree_base_widths.get(col, 1) for col in self._tree_columns)
        if total_base <= 0:
            return
        width = max(event.width - 20, 500)
        for col in self._tree_columns:
            ratio = self._tree_base_widths.get(col, 1) / total_base
            target = int(width * ratio)
            self.tree.column(col, width=max(60, target), stretch=True)

    def _sort_column(self, col: str, reverse: bool) -> None:
        if self.tree is None:
            return
        items = []
        for item_id in self.tree.get_children(""):
            raw = self.tree.set(item_id, col)
            if col in ("cantidad", "dias"):
                try:
                    key = float(str(raw).replace(",", ""))
                except ValueError:
                    key = -999999.0
            elif col in ("f_venc",):
                parsed = self._parse_date(str(raw))
                key = parsed or date.min
            else:
                key = str(raw).lower()
            items.append((key, item_id))

        items.sort(reverse=reverse)
        for index, (_key, item_id) in enumerate(items):
            self.tree.move(item_id, "", index)
        self.tree.heading(col, command=lambda: self._sort_column(col, not reverse))

    def _status_for_days(self, days: int | None) -> str:
        if days is None:
            return "SIN FECHA"
        if days < 0:
            return "VENCIDO"
        if days <= 30:
            return "POR VENCER"
        return "VIGENTE"

    def _parse_date(self, value: str) -> date | None:
        raw = (value or "").strip()
        if not raw:
            return None

        formats = ["%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"]
        for fmt in formats:
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                continue

        return None

    def _extract_expiration_date(self, record: dict) -> date | None:
        candidate_keys = [
            "fecha_vencimiento",
            "f_vencimiento",
            "vencimiento",
            "fecha_venc",
            "fecha_vence",
        ]
        for key in candidate_keys:
            parsed = self._parse_date(str(record.get(key, "")))
            if parsed:
                return parsed
        return None

    def _build_row(self, record: dict, stock: float) -> tuple:
        exp = self._extract_expiration_date(record)
        days = (exp - date.today()).days if exp else None
        estado = self._status_for_days(days)

        return (
            substance_code(record, self.sustancias_by_id),
            substance_name(record, self.sustancias_by_id),
            record.get("lote", ""),
            exp.strftime("%Y-%m-%d") if exp else "",
            stock,
            self.lkp.to_name("unidades", record.get("id_unidad")) or record.get("unidad", ""),
            self.lkp.to_name("proveedores", record.get("id_proveedor")) or record.get("proveedor", record.get("fabricante", "")),
            days if days is not None else "",
            estado,
        )

    def _safe_float(self, value) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _compute_stock_map(self) -> dict[tuple[object, str], float]:
        """Calcula stock por (id_sustancia, lote) = Sum(entradas.total) - Sum(salidas.cantidad)."""
        entradas = DataHandler.get_all(ENTRADAS_FILE, "entradas")
        salidas = DataHandler.get_all(SALIDAS_FILE, "salidas")

        smap: dict[tuple[object, str], float] = {}
        for r in entradas:
            if r.get("anulado", False):
                continue
            key = (r.get("id_sustancia", r.get("codigo", "")), str(r.get("lote", "")).strip())
            smap[key] = smap.get(key, 0.0) + self._safe_float(r.get("total", 0))
        for r in salidas:
            if r.get("anulado", False):
                continue
            key = (r.get("id_sustancia", r.get("codigo", "")), str(r.get("lote", "")).strip())
            smap[key] = smap.get(key, 0.0) - self._safe_float(r.get("cantidad", 0))
        return smap

    def load_table(self) -> None:
        if self.tree is None:
            return

        query = self.search_var.get().strip().lower()
        entradas = DataHandler.get_all(ENTRADAS_FILE, "entradas")
        stock_map = self._compute_stock_map()

        # Agrupar entradas por (codigo, lote) para mostrar una fila por combinación
        seen: set[tuple[object, str]] = set()
        unique_records: list[tuple[dict, float]] = []
        for record in entradas:
            if record.get("anulado", False):
                continue
            key = (record.get("id_sustancia", record.get("codigo", "")), str(record.get("lote", "")).strip())
            if key not in seen:
                seen.add(key)
                unique_records.append((record, round(stock_map.get(key, 0.0), 6)))

        filtered_rows: list[tuple[tuple, dict]] = []
        for record, stock in unique_records:
            row = self._build_row(record, stock)
            if query and query not in str(row).lower():
                continue
            filtered_rows.append((row, record))

        if self.sort_mode == "dias":
            def _dias_key(pair: tuple[tuple, dict]) -> int:
                raw = str(pair[0][7]).strip()
                if raw in ("", "None"):
                    return 999999
                try:
                    return int(float(raw))
                except (TypeError, ValueError):
                    return 999999

            filtered_rows.sort(key=_dias_key)
        elif self.sort_mode == "fecha":
            filtered_rows.sort(key=lambda pair: self._parse_date(str(pair[0][3])) or date.max)

        try:
            por_pagina = max(1, int(self.por_pagina_var.get().strip()))
        except ValueError:
            por_pagina = 50
            self.por_pagina_var.set("50")

        total = len(filtered_rows)
        self.total_paginas = max(1, (total + por_pagina - 1) // por_pagina)
        self.pagina_actual = max(1, min(self.pagina_actual, self.total_paginas))
        start = (self.pagina_actual - 1) * por_pagina
        end = start + por_pagina

        self.tree.delete(*self.tree.get_children())
        self.row_records.clear()
        for row, record in filtered_rows[start:end]:
            item_id = self.tree.insert("", tk.END, values=row)
            self.row_records[item_id] = record

        if self.pag_label is not None:
            self.pag_label.config(text=f"Página {self.pagina_actual} de {self.total_paginas}")

    def sort_by_days(self) -> None:
        self.sort_mode = "dias"
        self.pagina_actual = 1
        self.load_table()

    def sort_by_date(self) -> None:
        self.sort_mode = "fecha"
        self.pagina_actual = 1
        self.load_table()

    def _ir_pagina(self, pagina: int) -> None:
        if pagina < 1 or pagina > self.total_paginas:
            return
        self.pagina_actual = pagina
        self.load_table()

    def _cambiar_por_pagina(self) -> None:
        self.pagina_actual = 1
        self.load_table()

    def on_select(self, _event: tk.Event) -> None:
        if self.tree is None:
            return

        selected = self.tree.selection()
        if not selected:
            return

        values = self.tree.item(selected[0], "values")
        self.detail_vars["codigo"].set(values[0] if len(values) > 0 else "")
        self.detail_vars["nombre"].set(values[1] if len(values) > 1 else "")
        self.detail_vars["lote"].set(values[2] if len(values) > 2 else "")
        self.detail_vars["fecha_vencimiento"].set(values[3] if len(values) > 3 else "")
        self.detail_vars["cantidad"].set(values[4] if len(values) > 4 else "")
        self.detail_vars["unidad"].set(values[5] if len(values) > 5 else "")
        self.detail_vars["fabricante"].set(values[6] if len(values) > 6 else "")
        self.detail_vars["dias_restantes"].set(values[7] if len(values) > 7 else "")
        self.detail_vars["estado"].set(values[8] if len(values) > 8 else "")

        # Actualizar color del label Estado
        estado = values[8] if len(values) > 8 else ""
        if self.estado_label is not None:
            if estado == "VIGENTE":
                self.estado_label.config(text=estado, bg="#4CAF50", fg="white")
            elif estado == "POR VENCER":
                self.estado_label.config(text=estado, bg="#FFD600", fg="#333")
            elif estado == "VENCIDO":
                self.estado_label.config(text=estado, bg="#F44336", fg="white")
            else:
                self.estado_label.config(text=estado, bg="white", fg="#333")

    def _mover_stock(self) -> None:
        """Crea salidas para los productos seleccionados en la tabla (retiro por lote)."""
        original_cursor = self.window.cget("cursor")
        self.window.config(cursor="watch")
        self.window.update()
        if self.tree is None:
            self.window.config(cursor=original_cursor)
            return
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Mover Stock", "Selecciona al menos un producto de la tabla")
            self.window.config(cursor=original_cursor)
            return

        tipo_salida = self.tipo_salida_var.get().strip()
        if not tipo_salida:
            messagebox.showwarning("Mover Stock", "Selecciona un Tipo de Salida")
            self.window.config(cursor=original_cursor)
            return

        observaciones = ""
        if self.obs_text is not None:
            observaciones = self.obs_text.get("1.0", tk.END).strip()

        items = []
        for item_id in selected:
            values = self.tree.item(item_id, "values")
            if len(values) < 9:
                continue
            codigo = str(values[0]).strip()
            nombre = str(values[1]).strip()
            lote = str(values[2]).strip()
            try:
                cantidad = float(values[4])
            except (TypeError, ValueError):
                cantidad = 0.0
            unidad = str(values[5]).strip()
            raw_record = self.row_records.get(item_id, {})
            sustancia = self.sustancias_by_id.get(raw_record.get("id_sustancia"), {})
            if not sustancia or not bool(sustancia.get("habilitada", True)):
                messagebox.showwarning("Validación", f"La sustancia {codigo} está inhabilitada")
                continue
            if cantidad <= 0:
                continue
            items.append({
                "codigo": codigo, "nombre": nombre, "lote": lote,
                "cantidad": cantidad, "unidad": unidad,
                "record": raw_record,
            })

        if not items:
            messagebox.showwarning("Mover Stock", "Los productos seleccionados no tienen stock disponible")
            self.window.config(cursor=original_cursor)
            return

        resumen = "\n".join(f"  {it['codigo']} - {it['nombre']} | Lote: {it['lote']} | Cant: {it['cantidad']}" for it in items)
        if not messagebox.askyesno(
            "Confirmar Mover Stock",
            f"Se crearán {len(items)} salida(s) tipo '{tipo_salida}':\n\n{resumen}\n\n¿Continuar?",
        ):
            self.window.config(cursor=original_cursor)
            return

        fecha_hoy = date.today().strftime("%Y-%m-%d")
        for it in items:
            raw_record = it.get("record", {})
            salida = {
                "fecha_salida": fecha_hoy,
                "id_tipo_salida": self.lkp.to_id("tipos_salida", tipo_salida),
                "id_sustancia": raw_record.get("id_sustancia"),
                "lote": it["lote"],
                "cantidad": it["cantidad"],
                "id_unidad": self.lkp.to_id("unidades", it["unidad"]),
                "densidad": "",
                "ubicacion_origen_tipo": raw_record.get("ubicacion_tipo", ""),
                "id_ubicacion_origen": raw_record.get("id_ubicacion"),
                "peso_inicial": "",
                "peso_final": "",
                "liquido": False,
                "en_uso": False,
                "observaciones": observaciones,
            }
            DataHandler.add_record(SALIDAS_FILE, "salidas", salida)
            registrar_bitacora(
                usuario=self.usuario,
                tipo_operacion="Salida",
                hoja=tipo_salida,
                id_registro=str(salida.get("id", "")),
                campo="mover_stock_vigencia",
                valor_anterior="",
                valor_nuevo=f"{it['codigo']} | Lote: {it['lote']} | Cant: {it['cantidad']}",
            )

        sync_inventario(ENTRADAS_FILE, SALIDAS_FILE, INVENTARIO_FILE)
        messagebox.showinfo("Mover Stock", f"Se registraron {len(items)} salida(s) correctamente")
        self.load_table()
        self.window.config(cursor=original_cursor)

    def remove_selected(self) -> None:
        if self.tree is None:
            return
        for item in self.tree.selection():
            self.tree.delete(item)

    def clear(self) -> None:
        self.search_var.set("")
        self.sort_mode = "default"
        self.pagina_actual = 1
        for var in self.detail_vars.values():
            var.set("")
        if self.estado_label is not None:
            self.estado_label.config(text="", bg="white", fg="#333")
        self.tipo_salida_var.set("")
        if self.obs_text is not None:
            self.obs_text.delete("1.0", tk.END)
        self.load_table()