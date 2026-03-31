import tkinter as tk
from tkinter import ttk

from config.config import COLORS, ENTRADAS_FILE, SALIDAS_FILE
from utils.data_handler import DataHandler


class StockWindow:
    """Vista de stock calculado: Entradas - Salidas por producto+lote."""

    def __init__(self, parent: tk.Tk):
        self.window = tk.Toplevel(parent)
        self.window.title("Stock")
        self.window.geometry("1300x560")
        self.window.configure(bg=COLORS["secondary"])

        self.search_var = tk.StringVar()
        self.tree: ttk.Treeview | None = None

        self._build_ui()
        self.load_table()

    def _build_ui(self) -> None:
        wrapper = tk.Frame(self.window, bg="white", bd=1, relief="solid", padx=12, pady=12)
        wrapper.pack(expand=True, fill="both", padx=14, pady=14)

        tk.Label(
            wrapper,
            text="Stock",
            bg=COLORS["primary"],
            fg=COLORS["text_light"],
            font=("Segoe UI", 16, "bold"),
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
        ).pack(side="left")

        columns = (
            "codigo", "nombre", "lote", "unidad", "presentacion",
            "entrada", "salida", "stock", "ubicacion", "fv", "proveedor",
        )
        self.tree = ttk.Treeview(wrapper, columns=columns, show="headings", height=14)
        self.tree.pack(expand=True, fill="both")

        headings = {
            "codigo": "Código",
            "nombre": "Nombre",
            "lote": "Lote",
            "unidad": "Unidad",
            "presentacion": "Presentación",
            "entrada": "Entrada",
            "salida": "Salida",
            "stock": "Stock",
            "ubicacion": "Ubicación",
            "fv": "F. Vencimiento",
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
            "ubicacion": 110,
            "fv": 110,
            "proveedor": 130,
        }

        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w")

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

    def load_table(self) -> None:
        if self.tree is None:
            return

        query = self.search_var.get().strip().lower()
        entradas = DataHandler.get_all(ENTRADAS_FILE, "entradas")
        salidas = DataHandler.get_all(SALIDAS_FILE, "salidas")

        # Aggregate by (codigo, lote)
        stock_map: dict[tuple[str, str], dict] = {}

        for rec in entradas:
            if rec.get("anulado", False):
                continue
            codigo = str(rec.get("codigo", "")).strip()
            lote = str(rec.get("lote", "")).strip()
            key = (codigo, lote)
            total = self._safe_float(rec.get("total", 0))

            if key not in stock_map:
                stock_map[key] = {
                    "codigo": codigo,
                    "nombre": str(rec.get("nombre", "")),
                    "lote": lote,
                    "unidad": str(rec.get("unidad", "")),
                    "presentacion": str(rec.get("presentacion", "")),
                    "entrada": 0.0,
                    "salida": 0.0,
                    "ubicacion": str(rec.get("ubicacion", "")),
                    "fv": str(rec.get("fecha_vencimiento", "")),
                    "proveedor": str(rec.get("proveedor", rec.get("fabricante", ""))),
                }
            stock_map[key]["entrada"] += total

        for rec in salidas:
            if rec.get("anulado", False):
                continue
            codigo = str(rec.get("codigo", "")).strip()
            lote = str(rec.get("lote", "")).strip()
            key = (codigo, lote)
            qty = self._safe_float(rec.get("cantidad", 0))

            if key in stock_map:
                stock_map[key]["salida"] += qty

        self.tree.delete(*self.tree.get_children())

        for data in stock_map.values():
            stock = round(data["entrada"] - data["salida"], 6)
            row = (
                data["codigo"],
                data["nombre"],
                data["lote"],
                data["unidad"],
                data["presentacion"],
                data["entrada"],
                data["salida"],
                stock,
                data["ubicacion"],
                data["fv"],
                data["proveedor"],
            )

            if query and query not in str(row).lower():
                continue

            self.tree.insert("", tk.END, values=row)
