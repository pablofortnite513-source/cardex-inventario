import tkinter as tk
from tkinter import ttk

from config.config import COLORS, INVENTARIO_FILE
from utils.data_handler import DataHandler


class StockWindow:
    """Vista de stock consolidada desde inventario.json."""

    def __init__(self, parent: tk.Tk):
        self.window = tk.Toplevel(parent)
        self.window.title("Stock")
        self.window.geometry("1100x560")
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

        columns = ("codigo", "nombre", "cantidad", "unidad", "stock", "proveedor", "cantidad_minima")
        self.tree = ttk.Treeview(wrapper, columns=columns, show="headings", height=14)
        self.tree.pack(expand=True, fill="both")

        headings = {
            "codigo": "Codigo",
            "nombre": "Nombre",
            "cantidad": "Cantidad",
            "unidad": "Unidad",
            "stock": "Stock",
            "proveedor": "Proveedor",
            "cantidad_minima": "Cantidad Minima",
        }
        widths = {
            "codigo": 90,
            "nombre": 310,
            "cantidad": 110,
            "unidad": 90,
            "stock": 110,
            "proveedor": 170,
            "cantidad_minima": 150,
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

    def load_table(self) -> None:
        if self.tree is None:
            return

        query = self.search_var.get().strip().lower()
        records = DataHandler.get_all(INVENTARIO_FILE, "inventario")

        self.tree.delete(*self.tree.get_children())

        for item in records:
            row = (
                item.get("codigo", ""),
                item.get("nombre", ""),
                item.get("cantidad", 0),
                item.get("unidad", ""),
                item.get("stock", item.get("cantidad", 0)),
                item.get("proveedor", ""),
                item.get("cantidad_minima", 0),
            )

            if query and query not in str(row).lower():
                continue

            self.tree.insert("", tk.END, values=row)
