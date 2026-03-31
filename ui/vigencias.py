import tkinter as tk
from datetime import date, datetime
from tkinter import ttk

from config.config import COLORS, ENTRADAS_FILE, SALIDAS_FILE
from utils.data_handler import DataHandler


class VigenciasWindow:
    """Vista de vigencias de inventario con dias restantes y estado."""

    def __init__(self, parent: tk.Tk):
        self.window = tk.Toplevel(parent)
        self.window.title("Sistema de Gestion - Vigencias")
        self.window.geometry("1260x680")
        self.window.configure(bg=COLORS["secondary"])

        self.search_var = tk.StringVar()
        self.tree: ttk.Treeview | None = None
        self.estado_label: tk.Label | None = None

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

        self._build_ui()
        self.load_table()

    def _build_ui(self) -> None:
        wrapper = tk.Frame(self.window, bg="white", bd=1, relief="solid", padx=12, pady=12)
        wrapper.pack(expand=True, fill="both", padx=14, pady=14)

        tk.Label(
            wrapper,
            text="Sistema de Gestion - Vigencias",
            bg=COLORS["primary"],
            fg=COLORS["text_light"],
            font=("Segoe UI", 18, "bold"),
            pady=6,
        ).pack(fill="x", pady=(0, 10))

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
        self.tree = ttk.Treeview(wrapper, columns=columns, show="headings", height=12)
        self.tree.pack(expand=True, fill="both", pady=(0, 10))
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

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
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w")

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
                tk.Entry(group, textvariable=self.detail_vars[key], state="readonly").pack(fill="x")

        for col in range(3):
            details.columnconfigure(col, weight=1)

        button_row = tk.Frame(wrapper, bg="white")
        button_row.pack(fill="x", pady=(10, 0))

        tk.Button(
            button_row,
            text="Quitar Lista",
            command=self.remove_selected,
            bg=COLORS["primary"],
            fg=COLORS["text_light"],
            relief="flat",
            padx=18,
            pady=6,
        ).pack(side="right", padx=(8, 0))
        tk.Button(
            button_row,
            text="Limpiar",
            command=self.clear,
            bg=COLORS["primary"],
            fg=COLORS["text_light"],
            relief="flat",
            padx=18,
            pady=6,
        ).pack(side="right", padx=(8, 0))
        tk.Button(
            button_row,
            text="Salir",
            command=self.window.destroy,
            bg=COLORS["primary"],
            fg=COLORS["text_light"],
            relief="flat",
            padx=18,
            pady=6,
        ).pack(side="right")

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
            record.get("codigo", ""),
            record.get("nombre", ""),
            record.get("lote", ""),
            exp.strftime("%Y-%m-%d") if exp else "",
            stock,
            record.get("unidad", ""),
            record.get("proveedor", record.get("fabricante", "")),
            days if days is not None else "",
            estado,
        )

    def _safe_float(self, value) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _compute_stock_map(self) -> dict[tuple[str, str], float]:
        """Calcula stock por (codigo, lote) = Sum(entradas.total) - Sum(salidas.cantidad)."""
        entradas = DataHandler.get_all(ENTRADAS_FILE, "entradas")
        salidas = DataHandler.get_all(SALIDAS_FILE, "salidas")

        smap: dict[tuple[str, str], float] = {}
        for r in entradas:
            if r.get("anulado", False):
                continue
            key = (str(r.get("codigo", "")).strip(), str(r.get("lote", "")).strip())
            smap[key] = smap.get(key, 0.0) + self._safe_float(r.get("total", 0))
        for r in salidas:
            if r.get("anulado", False):
                continue
            key = (str(r.get("codigo", "")).strip(), str(r.get("lote", "")).strip())
            smap[key] = smap.get(key, 0.0) - self._safe_float(r.get("cantidad", 0))
        return smap

    def load_table(self) -> None:
        if self.tree is None:
            return

        query = self.search_var.get().strip().lower()
        entradas = DataHandler.get_all(ENTRADAS_FILE, "entradas")
        stock_map = self._compute_stock_map()

        # Agrupar entradas por (codigo, lote) para mostrar una fila por combinación
        seen: set[tuple[str, str]] = set()
        unique_records: list[tuple[dict, float]] = []
        for record in entradas:
            if record.get("anulado", False):
                continue
            key = (str(record.get("codigo", "")).strip(), str(record.get("lote", "")).strip())
            if key not in seen:
                seen.add(key)
                unique_records.append((record, round(stock_map.get(key, 0.0), 6)))

        self.tree.delete(*self.tree.get_children())

        for record, stock in unique_records:
            row = self._build_row(record, stock)
            if query and query not in str(row).lower():
                continue
            self.tree.insert("", tk.END, values=row)

    def sort_by_days(self) -> None:
        if self.tree is None:
            return

        items = []
        for item_id in self.tree.get_children():
            values = self.tree.item(item_id, "values")
            days_raw = values[7] if len(values) > 7 else ""
            try:
                days = int(days_raw)
            except (TypeError, ValueError):
                days = 999999
            items.append((days, values))

        self.tree.delete(*self.tree.get_children())
        for _, row in sorted(items, key=lambda pair: pair[0]):
            self.tree.insert("", tk.END, values=row)

    def sort_by_date(self) -> None:
        if self.tree is None:
            return

        items = []
        for item_id in self.tree.get_children():
            values = self.tree.item(item_id, "values")
            date_raw = values[3] if len(values) > 3 else ""
            parsed = self._parse_date(str(date_raw))
            items.append((parsed or date.max, values))

        self.tree.delete(*self.tree.get_children())
        for _, row in sorted(items, key=lambda pair: pair[0]):
            self.tree.insert("", tk.END, values=row)

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

    def remove_selected(self) -> None:
        if self.tree is None:
            return
        for item in self.tree.selection():
            self.tree.delete(item)

    def clear(self) -> None:
        self.search_var.set("")
        for var in self.detail_vars.values():
            var.set("")
        if self.estado_label is not None:
            self.estado_label.config(text="", bg="white", fg="#333")
        self.load_table()