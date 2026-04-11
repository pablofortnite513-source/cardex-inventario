import tkinter as tk
from datetime import date
from tkinter import filedialog, messagebox

from config.config import (
    COLORS,
    ENTRADAS_FILE,
    PROVEEDORES_FILE,
    REPORTES_PATH,
    SALIDAS_FILE,
    SUSTANCIAS_FILE,
    TIPOS_ENTRADA_FILE,
    UBICACIONES_FILE,
    UBICACIONES_USO_FILE,
    UNIDADES_FILE,
)
from ui.styles import build_header
from utils.data_handler import (
    DataHandler,
    Lookups,
    build_location_indexes,
    build_substance_indexes,
    location_name,
    substance_cas,
    substance_code,
    substance_from_code,
    substance_name,
)

try:
    from openpyxl import load_workbook
except ImportError:
    load_workbook = None


class StockAnalistaWindow:
    """Genera reporte de stock para analista usando plantilla fija."""

    def __init__(self, parent: tk.Tk):
        self.window = tk.Toplevel(parent)
        self.window.title("Stock Analista")
        self.window.geometry("680x240")
        self.window.configure(bg=COLORS["secondary"])
        self._build_ui()

    def _build_ui(self) -> None:
        wrapper = tk.Frame(self.window, bg="white", bd=1, relief="solid", padx=12, pady=12)
        wrapper.pack(expand=True, fill="both", padx=14, pady=14)

        build_header(wrapper, "Sistema de Gestión  -  Stock Analista")

        tk.Label(
            wrapper,
            text="Genera un Excel continuo basado en template_reporteanalista.xlsx",
            bg="white",
            fg=COLORS["text_dark"],
            font=("Segoe UI", 10),
            anchor="w",
            justify="left",
        ).pack(fill="x", pady=(10, 16))

        actions = tk.Frame(wrapper, bg="white")
        actions.pack(fill="x")

        tk.Button(
            actions,
            text="Generar y guardar",
            command=self.generate_report,
            bg=COLORS["primary"],
            fg=COLORS["text_light"],
            relief="flat",
            padx=20,
            pady=7,
        ).pack(side="left")

        tk.Button(
            actions,
            text="Salir",
            command=self.window.destroy,
            bg=COLORS["border"],
            fg=COLORS["text_dark"],
            relief="flat",
            padx=20,
            pady=7,
        ).pack(side="right")

    def generate_report(self) -> None:
        if load_workbook is None:
            messagebox.showerror(
                "Dependencia faltante",
                "No se encontró openpyxl. Instala con: pip install openpyxl",
                parent=self.window,
            )
            return

        template_path = REPORTES_PATH / "templates" / "template_reporteanalista.xlsx"
        if not template_path.exists():
            messagebox.showerror(
                "Plantilla no encontrada",
                f"No existe la plantilla:\n{template_path}",
                parent=self.window,
            )
            return

        default_name = f"stock_analista_{date.today().strftime('%Y%m%d')}.xlsx"
        save_path = filedialog.asksaveasfilename(
            title="Guardar reporte Stock Analista",
            initialfile=default_name,
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            initialdir=str(REPORTES_PATH),
            parent=self.window,
        )
        if not save_path:
            return

        try:
            data_rows = _build_stock_analista_rows()
            _render_stock_analista_sheet(template_path, save_path, data_rows)
            messagebox.showinfo(
                "Reporte generado",
                f"Excel generado correctamente:\n{save_path}",
                parent=self.window,
            )
        except Exception as e:
            messagebox.showerror(
                "Error al guardar",
                f"No se pudo generar el reporte:\n{e}",
                parent=self.window,
            )


def _safe_float(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _build_stock_analista_rows() -> list[list]:
    entradas = DataHandler.get_all(ENTRADAS_FILE, "entradas")
    salidas = DataHandler.get_all(SALIDAS_FILE, "salidas")

    unidades_cat = DataHandler.load_json(UNIDADES_FILE).get("maestrasUnidades", [])
    proveedores_cat = DataHandler.load_json(PROVEEDORES_FILE).get("maestrasProveedores", [])
    sustancias_cat = DataHandler.load_json(SUSTANCIAS_FILE).get("maestrasSustancias", [])
    ubicaciones_cat = DataHandler.load_json(UBICACIONES_FILE).get("maestrasUbicaciones", [])
    ubicaciones_uso_cat = DataHandler.load_json(UBICACIONES_USO_FILE).get("maestrasUbicacionesUso", [])
    tipos_entrada_cat = DataHandler.load_json(TIPOS_ENTRADA_FILE).get("maestrasTiposEntrada", [])

    lkp = Lookups(unidades=unidades_cat, proveedores=proveedores_cat, tipos_entrada=tipos_entrada_cat)
    sustancias_by_id, sustancias_by_code = build_substance_indexes(sustancias_cat)
    locations_by_key, _ = build_location_indexes(ubicaciones_cat, ubicaciones_uso_cat)

    by_key: dict[tuple[object, str], dict] = {}

    for rec in entradas:
        if rec.get("anulado", False):
            continue

        substance_key = rec.get("id_sustancia", rec.get("codigo", ""))
        lote = str(rec.get("lote", "")).strip()
        key = (substance_key, lote)

        total_in = _safe_float(rec.get("total", rec.get("cantidad", 0)))

        if key not in by_key:
            by_key[key] = {
                "record": rec,
                "entrada": 0.0,
                "salida": 0.0,
                "en_uso": False,
            }

        by_key[key]["entrada"] += total_in

    for rec in salidas:
        if rec.get("anulado", False):
            continue

        substance_key = rec.get("id_sustancia", rec.get("codigo", ""))
        lote = str(rec.get("lote", "")).strip()
        key = (substance_key, lote)
        qty_out = _safe_float(rec.get("cantidad", 0))

        if key not in by_key:
            by_key[key] = {
                "record": rec,
                "entrada": 0.0,
                "salida": 0.0,
                "en_uso": False,
            }

        by_key[key]["salida"] += qty_out
        if qty_out > 0:
            by_key[key]["en_uso"] = True

    rows: list[list] = []
    for (_, lote), data in sorted(by_key.items(), key=lambda item: (str(item[0][0]), item[0][1])):
        record = data["record"]
        stock = round(data["entrada"] - data["salida"], 6)
        tipo_entrada = lkp.to_name("tipos_entrada", record.get("id_tipo_entrada"), "")
        lote_uso = "EN USO" if data["en_uso"] else ""

        cas = substance_cas(record, sustancias_by_id)
        if not cas:
            fallback = substance_from_code(sustancias_by_code, str(record.get("codigo", "")))
            if fallback is not None:
                cas = str(fallback.get("codigo_cas", ""))

        row = [
            substance_code(record, sustancias_by_id),
            cas,
            substance_name(record, sustancias_by_id),
            lote,
            lkp.to_name("unidades", record.get("id_unidad"), str(record.get("unidad", ""))),
            round(data["entrada"], 6),
            str(record.get("presentacion", "")),
            stock,
            location_name(record, locations_by_key),
            str(record.get("fecha_vencimiento", "")),
            lkp.to_name("proveedores", record.get("id_proveedor"), str(record.get("fabricante", record.get("proveedor", "")))),
            lote_uso,
            tipo_entrada,
            str(record.get("concentracion", "")),
            str(record.get("densidad", "")),
        ]
        rows.append(row)

    return rows


def _render_stock_analista_sheet(template_path, save_path, data_rows: list[list]) -> None:
    template_wb = load_workbook(template_path)
    ws = template_wb.active

    template_row = 2
    start_row = 2
    max_cols = 15

    style_templates = []
    for col in range(1, max_cols + 1):
        source = ws.cell(row=template_row, column=col)
        style_templates.append(
            {
                "font": source.font.copy() if source.font else None,
                "border": source.border.copy() if source.border else None,
                "fill": source.fill.copy() if source.fill else None,
                "number_format": source.number_format,
                "alignment": source.alignment.copy() if source.alignment else None,
            }
        )

    for i, row_data in enumerate(data_rows):
        current_row = start_row + i
        ws.insert_rows(current_row)

        for col, value in enumerate(row_data, start=1):
            target = ws.cell(row=current_row, column=col, value=value)
            if col <= len(style_templates):
                st = style_templates[col - 1]
                target.font = st["font"]
                target.border = st["border"]
                target.fill = st["fill"]
                target.number_format = st["number_format"]
                target.alignment = st["alignment"]

    if data_rows:
        ws.delete_rows(template_row + len(data_rows))

    template_wb.save(save_path)
