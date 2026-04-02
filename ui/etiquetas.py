import os
import tkinter as tk
from tkinter import Image, filedialog, messagebox, ttk

from config.config import COLORS, ENTRADAS_FILE, IMAGES_PATH, SUSTANCIAS_FILE
from utils.data_handler import DataHandler


def mm_to_px(mm: float, dpi: int = 300) -> int:
    return int((mm / 25.4) * dpi)


DPI = 300
BASE_LABEL_W = 640
BASE_LABEL_H = 405

# Medidas extraídas de Excel (LE-FO006_01) con escala de impresión 75%
# Ancho/alto base detectado en celdas A:H y filas 3:11, ajustado por escala 75%.
EXCEL_PRINT_SCALE = 0.75
LABEL_WIDTH_MM = 135.996 * EXCEL_PRINT_SCALE
LABEL_HEIGHT_MM = 101.406 * EXCEL_PRINT_SCALE
LABEL_W_PX = mm_to_px(LABEL_WIDTH_MM, DPI)
LABEL_H_PX = mm_to_px(LABEL_HEIGHT_MM, DPI)

# Hoja A4 física real en orientación horizontal (como Excel)
A4_W = mm_to_px(297, DPI)
A4_H = mm_to_px(210, DPI)

# Posiciones fijas (mm) según pitch de Excel con escala de impresión 75%
# Pitch horizontal: columnas A:I -> 138.377 mm * 0.75
# Pitch vertical: 12 filas (3..14) -> 119.398 mm * 0.75
START_X_MM = 3.0
START_Y_MM = 27.0
PITCH_X_MM = 138.377 * EXCEL_PRINT_SCALE
PITCH_Y_MM = 119.398 * EXCEL_PRINT_SCALE

LABEL_POSITIONS_MM = [
    (START_X_MM, START_Y_MM),
    (START_X_MM + PITCH_X_MM, START_Y_MM),
    (START_X_MM, START_Y_MM + PITCH_Y_MM),
    (START_X_MM + PITCH_X_MM, START_Y_MM + PITCH_Y_MM),
]

LABEL_POSITIONS_PX = [(mm_to_px(x, DPI), mm_to_px(y, DPI)) for x, y in LABEL_POSITIONS_MM]


class EtiquetasWindow:
    """Ventana de generación de etiquetas para frascos de productos."""

    def __init__(self, parent: tk.Tk):
        self.window = tk.Toplevel(parent)
        self.window.title("Imprimir Etiquetas")
        self.window.geometry("1200x720")
        self.window.configure(bg=COLORS["secondary"])

        self.codigo_var = tk.StringVar()
        self.nombre_var = tk.StringVar()

        # Detail fields
        self.det_codigo_var = tk.StringVar()
        self.det_nombre_var = tk.StringVar()
        self.det_lote_var = tk.StringVar()
        self.det_fv_var = tk.StringVar()
        self.det_fecha_var = tk.StringVar()
        self.det_unidad_var = tk.StringVar()
        self.det_concentracion_var = tk.StringVar()
        self.det_presentacion_var = tk.StringVar()
        self.det_proveedor_var = tk.StringVar()
        self.det_cas_var = tk.StringVar()
        self.det_ubicacion_var = tk.StringVar()
        self.det_condicion_var = tk.StringVar()
        self.det_cantidad_var = tk.StringVar(value="1")

        self.tree: ttk.Treeview | None = None
        self.codigo_combo: ttk.Combobox | None = None

        self._build_ui()
        self._bind_events()

    # ── datos ──────────────────────────────────────────────────

    def _get_entradas(self) -> list[dict]:
        return DataHandler.get_all(ENTRADAS_FILE, "entradas")

    def _get_sustancias(self) -> list[dict]:
        return DataHandler.load_json(SUSTANCIAS_FILE).get("maestrasSustancias", [])

    def _available_codes(self) -> list[str]:
        entradas = self._get_entradas()
        codes = {str(r.get("codigo", "")).strip() for r in entradas if str(r.get("codigo", "")).strip()}
        return sorted(codes)

    def _find_sustancia_cas(self, codigo: str) -> str:
        for s in self._get_sustancias():
            if str(s.get("codigo", "")).strip() == codigo:
                return str(s.get("codigo_cas", ""))
        return ""

    def _entries_for_code(self, codigo: str) -> list[dict]:
        return [
            r for r in self._get_entradas()
            if str(r.get("codigo", "")).strip() == codigo
        ]

    # ── UI ─────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        wrapper = tk.Frame(self.window, bg="white", bd=1, relief="solid", padx=14, pady=14)
        wrapper.pack(expand=True, fill="both", padx=14, pady=14)

        # Header
        header = tk.Frame(wrapper, bg=COLORS["primary"])
        header.pack(fill="x", pady=(0, 10))

        tk.Label(
            header, text="Etiquetas", bg=COLORS["primary"], fg=COLORS["text_light"],
            font=("Segoe UI", 22, "bold italic"), pady=6,
        ).pack(side="left", padx=12)

        tk.Label(
            header, text="CECIF", bg=COLORS["primary"], fg=COLORS["text_light"],
            font=("Segoe UI", 18, "bold"), pady=6,
        ).pack(side="right", padx=12)

        # ── Información a Buscar ──
        search = tk.LabelFrame(wrapper, text="Información a Buscar", bg="white", fg="#1F4F8A", font=("Segoe UI", 11, "bold"))
        search.pack(fill="x", padx=4, pady=(0, 8))

        search_row = tk.Frame(search, bg="white")
        search_row.pack(fill="x", padx=10, pady=8)

        code_frame = tk.Frame(search_row, bg="white")
        code_frame.pack(side="left", padx=(0, 12))
        tk.Label(code_frame, text="Codigo", bg="white", font=("Segoe UI", 10)).pack(anchor="w")
        self.codigo_combo = ttk.Combobox(
            code_frame, textvariable=self.codigo_var,
            values=self._available_codes(), state="readonly", width=12,
        )
        self.codigo_combo.pack(pady=(4, 0))

        name_frame = tk.Frame(search_row, bg="white")
        name_frame.pack(side="left", fill="x", expand=True)
        tk.Label(name_frame, text="Nombre del Producto", bg="white", font=("Segoe UI", 10)).pack(anchor="w")
        tk.Entry(name_frame, textvariable=self.nombre_var, state="readonly", font=("Segoe UI", 10)).pack(fill="x", pady=(4, 0))

        # ── Tabla de entradas ──
        columns = (
            "lote", "fecha", "fv", "unidad", "concentracion",
            "presentacion", "proveedor", "cas", "ubicacion", "almacenamiento",
        )
        self.tree = ttk.Treeview(wrapper, columns=columns, show="headings", height=6)
        self.tree.pack(fill="x", padx=4, pady=(0, 10))

        headings = {
            "lote": "Lote", "fecha": "F. Entrada", "fv": "F. Vencimiento",
            "unidad": "Unidad", "concentracion": "Concentración",
            "presentacion": "Presentación", "proveedor": "Proveedor",
            "cas": "CAS", "ubicacion": "Ubicación", "almacenamiento": "Almacenamiento",
        }
        widths = {
            "lote": 100, "fecha": 90, "fv": 95, "unidad": 60,
            "concentracion": 90, "presentacion": 85, "proveedor": 100,
            "cas": 90, "ubicacion": 80, "almacenamiento": 200,
        }
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths.get(col, 90), anchor="w")

        scrollbar = ttk.Scrollbar(wrapper, orient="horizontal", command=self.tree.xview)
        self.tree.configure(xscrollcommand=scrollbar.set)
        scrollbar.pack(fill="x", padx=4)

        # ── Detalle del producto seleccionado ──
        detail = tk.Frame(wrapper, bg="white")
        detail.pack(fill="x", padx=4, pady=(10, 0))

        # Row 1: Codigo, Nombre, Lote, F. Vencimiento, F. Entrada
        r1 = tk.Frame(detail, bg="white")
        r1.pack(fill="x", pady=(0, 6))
        self._add_detail(r1, "Codigo", self.det_codigo_var, 0)
        self._add_detail(r1, "Nombre del Producto", self.det_nombre_var, 1, weight=3)
        self._add_detail(r1, "Lote", self.det_lote_var, 2)
        self._add_detail(r1, "F. Vencimiento", self.det_fv_var, 3)
        self._add_detail(r1, "F. Entrada", self.det_fecha_var, 4)

        # Row 2: Unidad, Concentracion, Presentacion, Proveedor, CAS
        r2 = tk.Frame(detail, bg="white")
        r2.pack(fill="x", pady=(0, 6))
        self._add_detail(r2, "Unidad", self.det_unidad_var, 0)
        self._add_detail(r2, "Concentración", self.det_concentracion_var, 1)
        self._add_detail(r2, "Presentación", self.det_presentacion_var, 2)
        self._add_detail(r2, "Nombre del Proveedor", self.det_proveedor_var, 3, weight=2)
        self._add_detail(r2, "CAS", self.det_cas_var, 4)

        # Row 3: Ubicacion, Condicion, Cantidad + Crear/Salir
        r3 = tk.Frame(detail, bg="white")
        r3.pack(fill="x", pady=(0, 6))
        self._add_detail(r3, "Ubicación", self.det_ubicacion_var, 0)
        self._add_detail(r3, "Condición", self.det_condicion_var, 1, weight=3)

        # Crear section
        crear_frame = tk.LabelFrame(r3, text="Crear", bg="white", fg="#1F4F8A", font=("Segoe UI", 10, "bold"))
        crear_frame.grid(row=0, column=2, padx=8, sticky="ew")

        qty_frame = tk.Frame(crear_frame, bg="white")
        qty_frame.pack(side="left", padx=8, pady=6)
        tk.Label(qty_frame, text="Cantidad", bg="white", font=("Segoe UI", 9)).pack(anchor="w")
        tk.Entry(qty_frame, textvariable=self.det_cantidad_var, width=8, font=("Segoe UI", 10)).pack(pady=(2, 0))

        btn_frame = tk.Frame(crear_frame, bg="white")
        btn_frame.pack(side="right", padx=8, pady=6)
        tk.Button(
            btn_frame, text="Crear", command=self._crear_etiquetas,
            bg=COLORS["primary"], fg=COLORS["text_light"], relief="flat",
            font=("Segoe UI", 10, "bold"), padx=18, pady=4,
        ).pack(pady=(0, 4))
        tk.Button(
            btn_frame, text="Salir", command=self.window.destroy,
            bg=COLORS["error"], fg=COLORS["text_light"], relief="flat",
            font=("Segoe UI", 10, "bold"), padx=18, pady=4,
        ).pack()

        r3.columnconfigure(0, weight=1)
        r3.columnconfigure(1, weight=3)
        r3.columnconfigure(2, weight=2)

    def _add_detail(
        self, parent: tk.Frame, label: str, variable: tk.StringVar,
        col: int, weight: int = 1,
    ) -> None:
        frame = tk.Frame(parent, bg="white")
        frame.grid(row=0, column=col, padx=8, sticky="ew")
        tk.Label(frame, text=label, bg="white", font=("Segoe UI", 9)).pack(anchor="w")
        tk.Entry(frame, textvariable=variable, state="readonly", font=("Segoe UI", 10)).pack(fill="x", pady=(2, 0))
        parent.columnconfigure(col, weight=weight)

    # ── bindings ───────────────────────────────────────────────

    def _bind_events(self) -> None:
        if self.codigo_combo is not None:
            self.codigo_combo.bind("<<ComboboxSelected>>", self._on_code_selected)
        if self.tree is not None:
            self.tree.bind("<<TreeviewSelect>>", self._on_row_selected)

    def _on_code_selected(self, _event: tk.Event) -> None:
        codigo = self.codigo_var.get().strip()
        if not codigo:
            return

        entries = self._entries_for_code(codigo)
        if entries:
            self.nombre_var.set(str(entries[0].get("nombre", "")))
        else:
            self.nombre_var.set("")

        cas = self._find_sustancia_cas(codigo)
        self._populate_table(entries, cas)
        self._clear_details()

    def _populate_table(self, entries: list[dict], cas: str) -> None:
        if self.tree is None:
            return
        self.tree.delete(*self.tree.get_children())

        for rec in entries:
            row = (
                rec.get("lote", ""),
                rec.get("fecha", ""),
                rec.get("fecha_vencimiento", ""),
                rec.get("unidad", ""),
                rec.get("concentracion", ""),
                rec.get("presentacion", ""),
                rec.get("proveedor", rec.get("fabricante", "")),
                cas,
                rec.get("ubicacion", ""),
                rec.get("condicion_almacenamiento", ""),
            )
            self.tree.insert("", tk.END, values=row)

    def _on_row_selected(self, _event: tk.Event) -> None:
        if self.tree is None:
            return
        selection = self.tree.selection()
        if not selection:
            return

        values = self.tree.item(selection[0], "values")
        if not values or len(values) < 10:
            return

        self.det_codigo_var.set(self.codigo_var.get())
        self.det_nombre_var.set(self.nombre_var.get())
        self.det_lote_var.set(values[0])
        self.det_fecha_var.set(values[1])
        self.det_fv_var.set(values[2])
        self.det_unidad_var.set(values[3])
        self.det_concentracion_var.set(values[4])
        self.det_presentacion_var.set(values[5])
        self.det_proveedor_var.set(values[6])
        self.det_cas_var.set(values[7])
        self.det_ubicacion_var.set(values[8])
        self.det_condicion_var.set(values[9])

    def _clear_details(self) -> None:
        for var in (
            self.det_codigo_var, self.det_nombre_var, self.det_lote_var,
            self.det_fv_var, self.det_fecha_var, self.det_unidad_var,
            self.det_concentracion_var, self.det_presentacion_var,
            self.det_proveedor_var, self.det_cas_var, self.det_ubicacion_var,
            self.det_condicion_var,
        ):
            var.set("")

    # ── generación de etiquetas ────────────────────────────────

    def _crear_etiquetas(self) -> None:
        if not self.det_codigo_var.get().strip():
            messagebox.showwarning("Etiquetas", "Selecciona un registro de la tabla primero.")
            return

        try:
            cantidad = int(self.det_cantidad_var.get().strip() or "1")
            if cantidad < 1 or cantidad > 20:
                raise ValueError
        except ValueError:
            messagebox.showerror("Etiquetas", "Cantidad debe ser un número entero entre 1 y 20.")
            return

        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            messagebox.showerror(
                "Etiquetas",
                "Se requiere la librería Pillow.\nInstala con: pip install Pillow",
            )
            return

        label_data = {
            "nombre": self.det_nombre_var.get(),
            "codigo": self.det_codigo_var.get(),
            "lote": self.det_lote_var.get(),
            "cas": self.det_cas_var.get(),
            "concentracion": self.det_concentracion_var.get(),
            "presentacion": self.det_presentacion_var.get(),
            "unidad": self.det_unidad_var.get(),
            "proveedor": self.det_proveedor_var.get(),
            "fv": self.det_fv_var.get(),
            "fecha_entrada": self.det_fecha_var.get(),
            "ubicacion": self.det_ubicacion_var.get(),
            "condicion": self.det_condicion_var.get(),
        }

        # Generate label image
        img = self._generate_label_image(label_data, Image, ImageDraw, ImageFont)

        # Ask where to save
        save_path = filedialog.asksaveasfilename(
            parent=self.window,
            title=f"Guardar etiqueta(s) - {cantidad} copia(s)",
            defaultextension=".pdf",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("PDF", "*.pdf")],
            initialfile=f"Etiqueta_{label_data['codigo']}_{label_data['lote']}",
        )
        if not save_path:
            return

        pages = self._build_a4_pages(img, cantidad, Image)

        if save_path.lower().endswith(".pdf"):
            self._save_as_pdf(pages, save_path)
        else:
            ext = os.path.splitext(save_path)[1].lower()
            if len(pages) == 1:
                if ext in (".jpg", ".jpeg"):
                    pages[0].save(save_path, quality=98, subsampling=0, dpi=(300, 300))
                else:
                    pages[0].save(save_path, dpi=(300, 300))
            else:
                base, _ = os.path.splitext(save_path)
                for idx, page_img in enumerate(pages, 1):
                    page_path = f"{base}_p{idx}{ext}"
                    if ext in (".jpg", ".jpeg"):
                        page_img.save(page_path, quality=98, subsampling=0, dpi=(300, 300))
                    else:
                        page_img.save(page_path, dpi=(300, 300))

        messagebox.showinfo("Etiquetas", f"Etiqueta(s) guardada(s) en:\n{save_path}")

    def _generate_label_image(self, data: dict, Image, ImageDraw, ImageFont):
        """Genera una etiqueta con layout compacto y colores como el formato de referencia."""
        from PIL import ImageOps

        # Se dibuja en la base original para conservar el layout sin deformarlo.
        W = BASE_LABEL_W
        H = BASE_LABEL_H
        img = Image.new("RGB", (W, H), "white")
        draw = ImageDraw.Draw(img)

        c_border = "#1F1F1F"
        c_gray = "#E7E7E7"
        c_white = "#FFFFFF"
        c_peach = "#EFC3A4"

        # Fuentes
        try:
            font_header = ImageFont.truetype("arialbd.ttf", 14)
            font_sub = ImageFont.truetype("arial.ttf", 10)
            font_label = ImageFont.truetype("arialbd.ttf", 9)
            font_value = ImageFont.truetype("arial.ttf", 11)
            font_name = ImageFont.truetype("arialbd.ttf", 28)
            font_code_label = ImageFont.truetype("arial.ttf", 9)
            font_cond = ImageFont.truetype("arial.ttf", 10)
            font_big = ImageFont.truetype("arialbd.ttf", 42)
        except (OSError, IOError):
            font_header = ImageFont.load_default()
            font_sub = font_header
            font_label = font_header
            font_value = font_header
            font_name = font_header
            font_code_label = font_header
            font_cond = font_header
            font_big = font_header

        def center_text(text: str, left: int, top: int, right: int, bottom: int, font, fill=c_border):
            bbox = draw.textbbox((0, 0), text, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            tx = left + max(0, (right - left - tw) // 2)
            ty = top + max(0, (bottom - top - th) // 2)
            draw.text((tx, ty), text, fill=fill, font=font)

        def wrap_text(value: str, max_chars: int) -> list[str]:
            words = value.split()
            if not words:
                return []
            lines: list[str] = []
            line = ""
            for word in words:
                proposal = f"{line} {word}".strip()
                if len(proposal) <= max_chars:
                    line = proposal
                else:
                    if line:
                        lines.append(line)
                    line = word
            if line:
                lines.append(line)
            return lines

        m = 8
        x0, y0 = m, m
        x1, y1 = W - m, H - m

        # Columnas principales
        code_col = x1 - 70
        left_label_end = x0 + 126
        right_label_start = x0 + 310
        right_value_start = x0 + 425
        logo_end = x0 + 126

        y = y0
        h1 = 22
        h2 = 20
        h_name = 50
        h_row = 30
        h_head_bottom = 22
        h_bottom = 92

        # Bloque superior: logo (celda fusionada 2 filas) + encabezados
        top_h = h1 + h2
        draw.rectangle([x0, y, x1, y + top_h], fill=c_white, outline=c_border, width=1)
        draw.line([logo_end, y, logo_end, y + top_h], fill=c_border, width=1)
        draw.line([logo_end, y + h1, x1, y + h1], fill=c_border, width=1)

        logo_path = IMAGES_PATH / "imgLogocecif.png"
        try:
            logo = Image.open(logo_path).convert("RGB")
            logo_fit = ImageOps.fit(logo, (logo_end - x0 - 2, top_h - 2), method=Image.Resampling.LANCZOS)
            img.paste(logo_fit, (x0 + 1, y + 1))
        except Exception:
            draw.text((x0 + 8, y + (top_h // 2) - 8), "CECIF", fill=c_border, font=font_header)

        center_text("IDENTIFICACION DE REACTIVO", logo_end, y, x1, y + h1, font_header)

        # Fila 2 (solo zona derecha): LE-FO | version | pagina
        t_w = x1 - logo_end
        s1 = logo_end + (t_w // 3)
        s2 = logo_end + ((t_w // 3) * 2)
        row2_y = y + h1
        draw.line([s1, row2_y, s1, row2_y + h2], fill=c_border, width=1)
        draw.line([s2, row2_y, s2, row2_y + h2], fill=c_border, width=1)
        center_text("LE-FO006/01", logo_end, row2_y, s1, row2_y + h2, font_sub)
        center_text("V4 / 2025-06-16", s1, row2_y, s2, row2_y + h2, font_sub)
        center_text("PAGINA 1 DE 1", s2, row2_y, x1, row2_y + h2, font_sub)
        y += top_h

        # Fila 3: Nombre + celda de etiqueta Codigo
        draw.rectangle([x0, y, x1, y + h_name], fill=c_white, outline=c_border, width=1)
        draw.line([code_col, y, code_col, y + h_name], fill=c_border, width=1)
        draw.rectangle([x0, y, left_label_end, y + h_name], fill=c_gray, outline=c_border, width=1)
        draw.rectangle([code_col, y, x1, y + h_name], fill=c_gray, outline=c_border, width=1)
        draw.text((x0 + 4, y + 4), "NOMBRE", fill=c_border, font=font_label)
        center_text("Codigo", code_col, y, x1, y + h_name, font_code_label)

        nombre = str(data.get("nombre", ""))
        name_bbox = draw.textbbox((0, 0), nombre, font=font_name)
        name_w = name_bbox[2] - name_bbox[0]
        fit_name = font_name
        if name_w > (code_col - left_label_end - 12):
            try:
                fit_name = ImageFont.truetype("arialbd.ttf", 18)
            except (OSError, IOError):
                fit_name = font_header
        center_text(nombre, left_label_end, y + 7, code_col, y + h_name, fit_name)
        y += h_name

        # Fila 4: Lote / Presentacion + Codigo (valor)
        draw.rectangle([x0, y, code_col, y + h_row], fill=c_white, outline=c_border, width=1)
        draw.rectangle([code_col, y, x1, y + h_row], fill=c_white, outline=c_border, width=1)
        draw.line([left_label_end, y, left_label_end, y + h_row], fill=c_border, width=1)
        draw.line([right_label_start, y, right_label_start, y + h_row], fill=c_border, width=1)
        draw.line([right_value_start, y, right_value_start, y + h_row], fill=c_border, width=1)
        draw.rectangle([x0, y, left_label_end, y + h_row], fill=c_gray, outline=c_border, width=1)
        draw.rectangle([right_label_start, y, right_value_start, y + h_row], fill=c_gray, outline=c_border, width=1)
        draw.text((x0 + 4, y + 4), "LOTE", fill=c_border, font=font_label)
        center_text(str(data.get("lote", "")), left_label_end, y, right_label_start, y + h_row, font_value)
        draw.text((right_label_start + 4, y + 4), "PRESENTACION", fill=c_border, font=font_label)
        center_text(str(data.get("presentacion", "")), right_value_start, y, code_col, y + h_row, font_value)

        code_text = str(data.get("codigo", ""))
        code_size = 40
        max_w = (x1 - code_col) - 8
        max_h = h_row - 6
        code_font = font_header
        while code_size >= 12:
            try:
                code_font = ImageFont.truetype("arialbd.ttf", code_size)
            except (OSError, IOError):
                code_font = font_header
            bbox_code = draw.textbbox((0, 0), code_text, font=code_font)
            text_w = bbox_code[2] - bbox_code[0]
            text_h = bbox_code[3] - bbox_code[1]
            if text_w <= max_w and text_h <= max_h:
                break
            code_size -= 2
        center_text(code_text, code_col, y, x1, y + h_row, code_font)
        y += h_row

        # Filas de datos
        rows = [
            ("FECHA VENCE", data.get("fv", ""), "UNIDAD DE MEDIDA", data.get("unidad", "")),
            ("CONCENTRACION", data.get("concentracion", ""), "FABRICANTE", data.get("proveedor", "")),
            ("FECHA INGRESO", data.get("fecha_entrada", ""), "CAS", data.get("cas", "")),
            ("FECHA DE APERTURA", "", "UBICACION STOCK:", ""),
        ]

        for left_lbl, left_val, right_lbl, right_val in rows:
            draw.rectangle([x0, y, x1, y + h_row], fill=c_white, outline=c_border, width=1)
            draw.line([left_label_end, y, left_label_end, y + h_row], fill=c_border, width=1)
            draw.line([right_label_start, y, right_label_start, y + h_row], fill=c_border, width=1)
            draw.line([right_value_start, y, right_value_start, y + h_row], fill=c_border, width=1)
            draw.rectangle([x0, y, left_label_end, y + h_row], fill=c_gray, outline=c_border, width=1)
            draw.rectangle([right_label_start, y, right_value_start, y + h_row], fill=c_gray, outline=c_border, width=1)
            draw.text((x0 + 4, y + 4), left_lbl, fill=c_border, font=font_label)
            center_text(str(left_val), left_label_end, y, right_label_start, y + h_row, font_value)
            draw.text((right_label_start + 4, y + 4), right_lbl, fill=c_border, font=font_label)
            center_text(str(right_val), right_value_start, y, x1, y + h_row, font_value)
            y += h_row

        # Encabezado inferior
        half = x0 + (x1 - x0) // 2
        draw.rectangle([x0, y, x1, y + h_head_bottom], fill=c_gray, outline=c_border, width=1)
        draw.line([half, y, half, y + h_head_bottom], fill=c_border, width=1)
        center_text("ALMACENAMIENTO", x0, y, half, y + h_head_bottom, font_label)
        center_text("UBICACION", half, y, x1, y + h_head_bottom, font_label)
        y += h_head_bottom

        # Fila final: izquierda blanca con texto + derecha durazno con ubicacion
        draw.rectangle([x0, y, half, y + h_bottom], fill=c_white, outline=c_border, width=1)
        draw.rectangle([half, y, x1, y + h_bottom], fill=c_peach, outline=c_border, width=1)
        lines = wrap_text(str(data.get("condicion", "")), 58)
        ty = y + 8
        for line in lines[:4]:
            draw.text((x0 + 8, ty), line, fill=c_border, font=font_cond)
            ty += 16

        center_text(str(data.get("ubicacion", "")), half, y, x1, y + h_bottom, font_big)

        return img.resize((LABEL_W_PX, LABEL_H_PX), resample=Image.Resampling.LANCZOS)

    def _build_a4_pages(self, label_img, cantidad: int, Image) -> list:
        """Crea páginas A4 reales con posiciones de etiqueta fijas en milímetros."""
        pages = []
        max_per_page = len(LABEL_POSITIONS_PX)

        for start in range(0, cantidad, max_per_page):
            page = Image.new("RGB", (A4_W, A4_H), "white")
            count = min(max_per_page, cantidad - start)
            for i in range(count):
                x, y = LABEL_POSITIONS_PX[i]
                page.paste(label_img, (x, y))
            pages.append(page)

        return pages

    def _save_as_pdf(self, pages: list, path: str) -> None:
        """Guarda páginas A4 en PDF a 300 DPI sin escalado automático."""
        if len(pages) == 1:
            pages[0].save(path, "PDF", resolution=300)
        else:
            pages[0].save(path, "PDF", resolution=300, save_all=True, append_images=pages[1:])
