import tkinter as tk
from datetime import date, datetime
from tkinter import ttk

from config.config import COLORS, ENTRADAS_FILE, PROVEEDORES_FILE, SALIDAS_FILE, SUSTANCIAS_FILE, UBICACIONES_FILE, UBICACIONES_USO_FILE, UNIDADES_FILE
from ui.styles import build_header
from utils.data_handler import DataHandler, Lookups, build_location_indexes, build_substance_indexes, location_name, substance_code, substance_name


class StockWindow:
    """Vista de stock calculado: Entradas - Salidas por producto+lote."""

    def __init__(self, parent: tk.Tk):
        self.window = tk.Toplevel(parent)
        self.window.title("Stock")
        self.window.geometry("1440x560")
        self.window.configure(bg=COLORS["secondary"])

        self.search_var = tk.StringVar()
        self.filter_ubicacion_var = tk.StringVar(value="Todos")
        self.filter_proveedor_var = tk.StringVar(value="Todos")
        self.filter_stock_estado_var = tk.StringVar(value="Todos")
        self.filter_vigencia_var = tk.StringVar(value="Todos")

        self.tree: ttk.Treeview | None = None
        self.filter_ubicacion_combo: ttk.Combobox | None = None
        self.filter_proveedor_combo: ttk.Combobox | None = None
        self.filter_stock_estado_combo: ttk.Combobox | None = None
        self.filter_vigencia_combo: ttk.Combobox | None = None
        self._tree_columns: tuple[str, ...] = ()
        self._tree_base_widths: dict[str, int] = {}
        self.pagina_actual = 1
        self.total_paginas = 1
        self.por_pagina_var = tk.StringVar(value="50")
        self.pag_label: tk.Label | None = None

        self._build_ui()
        self.window.bind("<Escape>", lambda _e: self.window.destroy())
        self.load_table()

    def _build_ui(self) -> None:
        wrapper = tk.Frame(self.window, bg="white", bd=1, relief="solid", padx=12, pady=12)
        wrapper.pack(expand=True, fill="both", padx=14, pady=14)

        build_header(wrapper, "Sistema de Gestión  -  Stock")

        search_row = tk.Frame(wrapper, bg="white")
        search_row.pack(fill="x", pady=(0, 8))

        search_entry = tk.Entry(search_row, textvariable=self.search_var)
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        search_entry.bind("<Return>", lambda e: self.load_table())
        tk.Button(
            search_row,
            text="Buscar",
            command=self.load_table,
            bg=COLORS["primary"],
            fg=COLORS["text_light"],
            relief="flat",
            padx=16,
            pady=5,
        ).pack(side="left")
        tk.Button(
            search_row,
            text="⟳ Refrescar",
            command=self.load_table,
            bg=COLORS["border"],
            fg=COLORS["text_dark"],
            relief="flat",
            padx=12,
            pady=5,
        ).pack(side="left", padx=(8, 0))

        tk.Button(
            search_row,
            text="Limpiar filtros",
            command=self._clear_filters,
            bg=COLORS["border"],
            fg=COLORS["text_dark"],
            relief="flat",
            padx=16,
            pady=5,
        ).pack(side="left", padx=(8, 0))

        filters_row = tk.Frame(wrapper, bg="white")
        filters_row.pack(fill="x", pady=(0, 8))

        tk.Label(filters_row, text="Ubicación", bg="white").pack(side="left")
        self.filter_ubicacion_combo = ttk.Combobox(filters_row, textvariable=self.filter_ubicacion_var, state="readonly", width=18)
        self.filter_ubicacion_combo.pack(side="left", padx=(4, 10))

        tk.Label(filters_row, text="Proveedor", bg="white").pack(side="left")
        self.filter_proveedor_combo = ttk.Combobox(filters_row, textvariable=self.filter_proveedor_var, state="readonly", width=18)
        self.filter_proveedor_combo.pack(side="left", padx=(4, 10))

        tk.Label(filters_row, text="Estado Stock", bg="white").pack(side="left")
        self.filter_stock_estado_combo = ttk.Combobox(
            filters_row,
            textvariable=self.filter_stock_estado_var,
            values=["Todos", "Sin stock", "Stock bajo", "Stock normal"],
            state="readonly",
            width=14,
        )
        self.filter_stock_estado_combo.pack(side="left", padx=(4, 10))

        tk.Label(filters_row, text="Vigencia", bg="white").pack(side="left")
        self.filter_vigencia_combo = ttk.Combobox(
            filters_row,
            textvariable=self.filter_vigencia_var,
            values=["Todos", "Vigente", "Por vencer", "Vencido"],
            state="readonly",
            width=12,
        )
        self.filter_vigencia_combo.pack(side="left", padx=(4, 0))

        for combo in (
            self.filter_ubicacion_combo,
            self.filter_proveedor_combo,
            self.filter_stock_estado_combo,
            self.filter_vigencia_combo,
        ):
            if combo is not None:
                combo.bind("<<ComboboxSelected>>", lambda _e: self.load_table())

        columns = (
            "codigo", "nombre", "lote", "unidad", "presentacion",
            "entrada", "salida", "stock", "cantidad", "ubicacion", "fv", "dias_vencer", "proveedor",
        )
        self._tree_columns = columns
        tree_frame = tk.Frame(wrapper, bg="white")
        tree_frame.pack(expand=True, fill="both")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=14)
        style = ttk.Style(self.window)
        style.configure("Treeview", background="white", foreground="black", rowheight=25, fieldbackground="white")
        style.map("Treeview", background=[("selected", COLORS["primary"])], foreground=[("selected", "white")])
        tree_scroll_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        tree_scroll_y.grid(row=0, column=1, sticky="ns")
        tree_scroll_x.grid(row=1, column=0, sticky="ew")

        headings = {
            "codigo": "Código",
            "nombre": "Nombre",
            "lote": "Lote",
            "unidad": "Unidad",
            "presentacion": "Presentación",
            "entrada": "Entrada",
            "salida": "Salida",
            "stock": "Stock",
            "cantidad": "Cantidad",
            "ubicacion": "Ubicación",
            "fv": "F. Vencimiento",
            "dias_vencer": "Días a Vencer",
            "proveedor": "Proveedor",
        }
        widths = {
            "codigo": 80,
            "nombre": 220,
            "lote": 90,
            "unidad": 70,
            "presentacion": 90,
            "entrada": 80,
            "salida": 80,
            "stock": 80,
            "cantidad": 180,
            "ubicacion": 110,
            "fv": 110,
            "dias_vencer": 100,
            "proveedor": 130,
        }

        for col in columns:
            self.tree.heading(col, text=headings[col], command=lambda c=col: self._sort_column(c, False))
            self.tree.column(col, width=widths[col], anchor="w", minwidth=max(60, int(widths[col] * 0.5)), stretch=True)
        self._tree_base_widths = widths
        self.tree.bind("<Configure>", self._on_tree_resize, add="+")

        # Colores solicitados
        self.tree.tag_configure("sin_stock", background="#FFCDD2")     # rojo
        self.tree.tag_configure("stock_bajo", background="#FFE0B2")    # naranja
        self.tree.tag_configure("por_vencer", background="#FFF9C4")    # amarillo
        self.tree.tag_configure("vencido", background="#EF9A9A")       # rojo vencido

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

        tk.Button(
            wrapper,
            text="Salir",
            command=self.window.destroy,
            bg=COLORS["primary"],
            fg=COLORS["text_light"],
            relief="flat",
            padx=24,
            pady=6,
        ).pack(pady=(10, 0))

    def _safe_float(self, value) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _parse_date(value: str) -> date | None:
        raw = (value or "").strip()
        if not raw:
            return None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                continue
        return None

    @staticmethod
    def _cantidad_label(stock: float, presentacion: str) -> str:
        """Devuelve texto de unidades enteras e iniciada a partir de stock/presentacion."""
        if not presentacion or presentacion.strip() == "":
            return ""
        try:
            pres = float(str(presentacion).replace(",", "."))
        except ValueError:
            return ""
        if pres <= 0:
            return ""
        cantidad = stock / pres
        enteras = int(cantidad)
        fraccion = cantidad - enteras
        if fraccion == 0:
            return f"{enteras} unidades enteras"
        return f"Hay {enteras} unidades enteras y 1 iniciada"

    def load_table(self) -> None:
        if self.tree is None:
            return

        query = self.search_var.get().strip().lower()
        entradas = DataHandler.get_all(ENTRADAS_FILE, "entradas")
        salidas = DataHandler.get_all(SALIDAS_FILE, "salidas")

        unidades_cat = DataHandler.load_json(UNIDADES_FILE).get("maestrasUnidades", [])
        proveedores_cat = DataHandler.load_json(PROVEEDORES_FILE).get("maestrasProveedores", [])
        sustancias_cat = DataHandler.load_json(SUSTANCIAS_FILE).get("maestrasSustancias", [])
        ubicaciones_cat = DataHandler.load_json(UBICACIONES_FILE).get("maestrasUbicaciones", [])
        ubicaciones_uso_cat = DataHandler.load_json(UBICACIONES_USO_FILE).get("maestrasUbicacionesUso", [])
        lkp = Lookups(unidades=unidades_cat, proveedores=proveedores_cat)
        sustancias_by_id, _ = build_substance_indexes(sustancias_cat)
        sustancias_habilitadas = {
            s.get("id"): bool(s.get("habilitada", True))
            for s in sustancias_cat
            if s.get("id") is not None
        }
        locations_by_key, _ = build_location_indexes(ubicaciones_cat, ubicaciones_uso_cat)

        sustancias_minimo: dict[object, float] = {
            s.get("id"): self._safe_float(s.get("cantidad_minima_stock", s.get("cantidad_minima", 0)))
            for s in sustancias_cat
            if s.get("id") is not None
        }

        # Aggregate by (id_sustancia, lote)
        stock_map: dict[tuple[object, str], dict] = {}

        for rec in entradas:
            if rec.get("anulado", False):
                continue
            substance_key = rec.get("id_sustancia", rec.get("codigo", ""))
            if not sustancias_habilitadas.get(substance_key, False):
                continue
            lote = str(rec.get("lote", "")).strip()
            key = (substance_key, lote)
            total = self._safe_float(rec.get("total", 0))

            if key not in stock_map:
                stock_map[key] = {
                    "record": rec,
                    "lote": lote,
                    "unidad": lkp.to_name("unidades", rec.get("id_unidad")) or str(rec.get("unidad", "")),
                    "presentacion": str(rec.get("presentacion", "")),
                    "entrada": 0.0,
                    "salida": 0.0,
                    "ubicacion": location_name(rec, locations_by_key),
                    "fv": str(rec.get("fecha_vencimiento", "")),
                    "proveedor": lkp.to_name("proveedores", rec.get("id_proveedor")) or str(rec.get("proveedor", rec.get("fabricante", ""))),
                }
            stock_map[key]["entrada"] += total

        for rec in salidas:
            if rec.get("anulado", False):
                continue
            substance_key = rec.get("id_sustancia", rec.get("codigo", ""))
            lote = str(rec.get("lote", "")).strip()
            key = (substance_key, lote)
            qty = self._safe_float(rec.get("cantidad", 0))

            if key in stock_map:
                stock_map[key]["salida"] += qty

        # Catálogos dinámicos para filtros
        ubicaciones_values = sorted({str(v.get("ubicacion", "")).strip() for v in stock_map.values() if str(v.get("ubicacion", "")).strip()})
        proveedores_values = sorted({str(v.get("proveedor", "")).strip() for v in stock_map.values() if str(v.get("proveedor", "")).strip()})
        if self.filter_ubicacion_combo is not None:
            self.filter_ubicacion_combo["values"] = ["Todos"] + ubicaciones_values
            if self.filter_ubicacion_var.get() not in self.filter_ubicacion_combo["values"]:
                self.filter_ubicacion_var.set("Todos")
        if self.filter_proveedor_combo is not None:
            self.filter_proveedor_combo["values"] = ["Todos"] + proveedores_values
            if self.filter_proveedor_var.get() not in self.filter_proveedor_combo["values"]:
                self.filter_proveedor_var.set("Todos")

        filtered_rows: list[tuple[tuple, tuple[str, ...]]] = []

        for data in stock_map.values():
            stock = round(data["entrada"] - data["salida"], 6)
            record = data["record"]
            minimo = sustancias_minimo.get(record.get("id_sustancia"), 0.0)

            if stock <= 0:
                estado_stock = "Sin stock"
            elif minimo > 0 and stock < minimo:
                estado_stock = "Stock bajo"
            else:
                estado_stock = "Stock normal"

            fv_date = self._parse_date(data["fv"])
            dias_vencer = ""
            estado_vigencia = "Vigente"
            if fv_date is not None:
                d = (fv_date - date.today()).days
                dias_vencer = str(d)
                if d < 0:
                    estado_vigencia = "Vencido"
                elif d <= 30:
                    estado_vigencia = "Por vencer"
                else:
                    estado_vigencia = "Vigente"
            fv_display = fv_date.strftime("%d-%m-%Y") if fv_date else ""

            if self.filter_ubicacion_var.get() != "Todos" and data["ubicacion"] != self.filter_ubicacion_var.get():
                continue
            if self.filter_proveedor_var.get() != "Todos" and data["proveedor"] != self.filter_proveedor_var.get():
                continue
            if self.filter_stock_estado_var.get() != "Todos" and estado_stock != self.filter_stock_estado_var.get():
                continue
            if self.filter_vigencia_var.get() != "Todos" and estado_vigencia != self.filter_vigencia_var.get():
                continue

            row = (
                substance_code(record, sustancias_by_id),
                substance_name(record, sustancias_by_id),
                data["lote"],
                data["unidad"],
                data["presentacion"],
                data["entrada"],
                data["salida"],
                stock,
                self._cantidad_label(stock, data["presentacion"]),
                data["ubicacion"],
                fv_display,
                dias_vencer,
                data["proveedor"],
            )

            if query and query not in str(row).lower():
                continue

            tags = ()
            if estado_vigencia == "Vencido":
                tags = ("vencido",)
            elif estado_stock == "Sin stock":
                tags = ("sin_stock",)
            elif estado_stock == "Stock bajo":
                tags = ("stock_bajo",)
            elif estado_vigencia == "Por vencer":
                tags = ("por_vencer",)

            filtered_rows.append((row, tags))

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
        for row, tags in filtered_rows[start:end]:
            self.tree.insert("", tk.END, values=row, tags=tags)

        if self.pag_label is not None:
            self.pag_label.config(text=f"Página {self.pagina_actual} de {self.total_paginas}")

    def _clear_filters(self) -> None:
        self.search_var.set("")
        self.filter_ubicacion_var.set("Todos")
        self.filter_proveedor_var.set("Todos")
        self.filter_stock_estado_var.set("Todos")
        self.filter_vigencia_var.set("Todos")
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

    def _on_tree_resize(self, event: tk.Event) -> None:
        if self.tree is None or not self._tree_columns:
            return
        total_base = sum(self._tree_base_widths.get(col, 1) for col in self._tree_columns)
        if total_base <= 0:
            return
        width = max(event.width - 20, 400)
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
            if col in ("entrada", "salida", "stock", "dias_vencer"):
                try:
                    key = float(str(raw).replace(",", ""))
                except ValueError:
                    key = -999999.0
            elif col in ("fv",):
                parsed = self._parse_date(str(raw))
                key = parsed or date.min
            else:
                key = str(raw).lower()
            items.append((key, item_id))

        items.sort(reverse=reverse)
        for index, (_key, item_id) in enumerate(items):
            self.tree.move(item_id, "", index)
        self.tree.heading(col, command=lambda: self._sort_column(col, not reverse))
