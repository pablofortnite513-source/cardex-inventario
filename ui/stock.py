import tkinter as tk
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
        self.tree: ttk.Treeview | None = None

        self._build_ui()
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

        columns = (
            "codigo", "nombre", "lote", "unidad", "presentacion",
            "entrada", "salida", "stock", "cantidad", "ubicacion", "fv", "proveedor",
        )
        tree_frame = tk.Frame(wrapper, bg="white")
        tree_frame.pack(expand=True, fill="both")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=14)
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
            "proveedor": 130,
        }

        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w", minwidth=widths[col])

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
        locations_by_key, _ = build_location_indexes(ubicaciones_cat, ubicaciones_uso_cat)

        # Aggregate by (id_sustancia, lote)
        stock_map: dict[tuple[object, str], dict] = {}

        for rec in entradas:
            if rec.get("anulado", False):
                continue
            substance_key = rec.get("id_sustancia", rec.get("codigo", ""))
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

        self.tree.delete(*self.tree.get_children())

        for data in stock_map.values():
            stock = round(data["entrada"] - data["salida"], 6)
            record = data["record"]
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
                data["fv"],
                data["proveedor"],
            )

            if query and query not in str(row).lower():
                continue

            self.tree.insert("", tk.END, values=row)
