import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from config.config import COLORS, ENTRADAS_FILE, IMAGES_PATH, SUSTANCIAS_FILE
from utils.data_handler import DataHandler


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
        return DataHandler.load_json(SUSTANCIAS_FILE).get("sustancias", [])

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
            if cantidad < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror("Etiquetas", "Cantidad debe ser un número entero mayor a 0.")
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
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("PDF", "*.pdf")],
            initialfile=f"Etiqueta_{label_data['codigo']}_{label_data['lote']}",
        )
        if not save_path:
            return

        if save_path.lower().endswith(".pdf"):
            self._save_as_pdf(img, save_path, cantidad, Image)
        else:
            if cantidad > 1:
                # Create a tiled image with multiple labels
                cols = min(cantidad, 2)
                rows_needed = (cantidad + cols - 1) // cols
                gap = 20
                full_w = cols * img.width + (cols + 1) * gap
                full_h = rows_needed * img.height + (rows_needed + 1) * gap
                full = Image.new("RGB", (full_w, full_h), "white")
                for i in range(cantidad):
                    r = i // cols
                    c = i % cols
                    x = gap + c * (img.width + gap)
                    y = gap + r * (img.height + gap)
                    full.paste(img, (x, y))
                full.save(save_path)
            else:
                img.save(save_path)

        messagebox.showinfo("Etiquetas", f"Etiqueta(s) guardada(s) en:\n{save_path}")

    def _generate_label_image(self, data: dict, Image, ImageDraw, ImageFont):
        """Genera una imagen de etiqueta estilo Excel IDENTIFICACIÓN DE REACTIVO."""
        W = 700
        H = 560
        img = Image.new("RGB", (W, H), "white")
        draw = ImageDraw.Draw(img)

        # Fuentes
        try:
            font_header = ImageFont.truetype("arialbd.ttf", 14)
            font_name = ImageFont.truetype("arialbd.ttf", 15)
            font_label = ImageFont.truetype("arialbd.ttf", 9)
            font_value = ImageFont.truetype("arial.ttf", 11)
            font_code_num = ImageFont.truetype("arialbd.ttf", 32)
            font_big = ImageFont.truetype("arialbd.ttf", 28)
            font_small = ImageFont.truetype("arial.ttf", 8)
            font_cond = ImageFont.truetype("arial.ttf", 10)
        except (OSError, IOError):
            font_header = ImageFont.load_default()
            font_name = font_header
            font_label = font_header
            font_value = font_header
            font_code_num = font_header
            font_big = font_header
            font_small = font_header
            font_cond = font_header

        M = 8
        x0 = M
        x1 = W - M

        # Posiciones de columnas
        logo_end = 150
        left_val = 130
        right_label = 350
        right_val = 500
        code_col = 620

        y = M

        # ── Fila 1: Encabezado (Logo + Título) ──
        hdr_h = 28
        draw.rectangle([x0, y, x1, y + hdr_h], outline="#333", width=1)
        draw.line([logo_end, y, logo_end, y + hdr_h], fill="#333", width=1)

        logo_path = IMAGES_PATH / "imagenppal.jpg"
        try:
            logo = Image.open(logo_path)
            logo.thumbnail((logo_end - x0 - 8, hdr_h - 4))
            img.paste(logo, (x0 + 4, y + (hdr_h - logo.size[1]) // 2))
        except Exception:
            draw.text((x0 + 10, y + 6), "CECIF", fill="#333", font=font_header)

        title = "IDENTIFICACIÓN DE REACTIVO"
        bbox_t = draw.textbbox((0, 0), title, font=font_header)
        tw = bbox_t[2] - bbox_t[0]
        title_area = x1 - logo_end
        draw.text((logo_end + (title_area - tw) // 2, y + 6), title, fill="#333", font=font_header)
        y += hdr_h

        # ── Fila 2: Sub-encabezado (LE-FO006/01 | V4/fecha | PÁGINA) ──
        sub_h = 18
        draw.rectangle([x0, y, x1, y + sub_h], outline="#333", width=1)
        draw.line([logo_end, y, logo_end, y + sub_h], fill="#333", width=1)

        sec_w = title_area // 3
        sec1 = logo_end
        sec2 = logo_end + sec_w
        sec3 = logo_end + sec_w * 2
        draw.line([sec2, y, sec2, y + sub_h], fill="#333", width=1)
        draw.line([sec3, y, sec3, y + sub_h], fill="#333", width=1)

        draw.text((sec1 + 8, y + 3), "LE-FO006/01", fill="#333", font=font_small)
        draw.text((sec2 + 8, y + 3), "V4", fill="#333", font=font_small)
        draw.text((sec3 + 8, y + 3), "PÁGINA 1 DE 1", fill="#333", font=font_small)
        y += sub_h

        # ── Fila 3: NOMBRE + Código ──
        name_h = 42
        draw.rectangle([x0, y, x1, y + name_h], outline="#333", width=1)
        draw.line([code_col, y, code_col, y + name_h], fill="#333", width=1)

        draw.text((x0 + 4, y + 4), "NOMBRE", fill="#333", font=font_label)

        nombre = data.get("nombre", "")
        bbox_n = draw.textbbox((0, 0), nombre, font=font_name)
        nw = bbox_n[2] - bbox_n[0]
        name_area = code_col - left_val
        draw.text((left_val + (name_area - nw) // 2, y + 18), nombre, fill="#333", font=font_name)

        draw.text((code_col + 4, y + 2), "Código", fill="#333", font=font_label)
        code_y_start = y + 14
        y += name_h

        # ── Fila 4: LOTE + PRESENTACIÓN (+ Código sigue a la derecha) ──
        row_h = 28
        draw.rectangle([x0, y, code_col, y + row_h], outline="#333", width=1)
        draw.rectangle([code_col, y, x1, y + row_h], outline="#333", width=1)
        draw.line([left_val, y, left_val, y + row_h], fill="#333", width=1)
        draw.line([right_label, y, right_label, y + row_h], fill="#333", width=1)
        draw.line([right_val, y, right_val, y + row_h], fill="#333", width=1)

        draw.text((x0 + 4, y + 3), "LOTE", fill="#333", font=font_label)
        draw.text((left_val + 8, y + 8), data.get("lote", ""), fill="#333", font=font_value)
        draw.text((right_label + 4, y + 3), "PRESENTACIÓN", fill="#333", font=font_label)
        draw.text((right_val + 8, y + 8), data.get("presentacion", ""), fill="#333", font=font_value)

        # Número de Código grande (abarca filas NOMBRE y LOTE)
        codigo = data.get("codigo", "")
        code_y_end = y + row_h
        code_area_w = x1 - code_col
        bbox_c = draw.textbbox((0, 0), codigo, font=font_code_num)
        cw = bbox_c[2] - bbox_c[0]
        ch = bbox_c[3] - bbox_c[1]
        code_center_y = code_y_start + (code_y_end - code_y_start - ch) // 2
        draw.text((code_col + (code_area_w - cw) // 2, code_center_y), codigo, fill="#333", font=font_code_num)
        y += row_h

        # ── Filas 5-8: Datos estándar ──
        data_rows = [
            ("FECHA VENCE", data.get("fv", ""), "UNIDAD DE MEDIDA", data.get("unidad", "")),
            ("CONCENTRACIÓN", data.get("concentracion", ""), "FABRICANTE", data.get("proveedor", "")),
            ("FECHA INGRESO", data.get("fecha_entrada", ""), "CAS", data.get("cas", "")),
            ("FECHA DE APERTURA", "", "UBICACIÓN STOCK:", data.get("ubicacion", "")),
        ]

        for left_lbl, left_v, right_lbl, right_v in data_rows:
            draw.rectangle([x0, y, x1, y + row_h], outline="#333", width=1)
            draw.line([left_val, y, left_val, y + row_h], fill="#333", width=1)
            draw.line([right_label, y, right_label, y + row_h], fill="#333", width=1)
            draw.line([right_val, y, right_val, y + row_h], fill="#333", width=1)

            draw.text((x0 + 4, y + 3), left_lbl, fill="#333", font=font_label)
            draw.text((left_val + 8, y + 8), left_v, fill="#333", font=font_value)
            draw.text((right_label + 4, y + 3), right_lbl, fill="#333", font=font_label)
            draw.text((right_val + 8, y + 8), right_v, fill="#333", font=font_value)
            y += row_h

        # ── Fila 9: Encabezados ALMACENAMIENTO | UBICACIÓN ──
        hdr_row_h = 20
        half = x0 + (x1 - x0) // 2
        draw.rectangle([x0, y, x1, y + hdr_row_h], outline="#333", width=1)
        draw.line([half, y, half, y + hdr_row_h], fill="#333", width=1)

        alm_text = "ALMACENAMIENTO"
        bbox_a = draw.textbbox((0, 0), alm_text, font=font_label)
        aw = bbox_a[2] - bbox_a[0]
        draw.text((x0 + ((half - x0) - aw) // 2, y + 5), alm_text, fill="#333", font=font_label)

        ubi_text = "UBICACIÓN"
        bbox_ub = draw.textbbox((0, 0), ubi_text, font=font_label)
        ubw = bbox_ub[2] - bbox_ub[0]
        draw.text((half + ((x1 - half) - ubw) // 2, y + 5), ubi_text, fill="#333", font=font_label)
        y += hdr_row_h

        # ── Fila 10: Condición (izq) + Ubicación grande (der) ──
        bot_h = 75
        draw.rectangle([x0, y, x1, y + bot_h], fill="#FDEBD0", outline="#333", width=1)
        draw.line([half, y, half, y + bot_h], fill="#333", width=1)

        # Texto condición (izquierda, word-wrap)
        cond = data.get("condicion", "")
        cond_x = x0 + 8
        cond_y = y + 8
        chars_per_line = (half - x0 - 16) // 6
        remaining = cond
        while remaining and cond_y < y + bot_h - 6:
            line_text = remaining[:chars_per_line]
            remaining = remaining[chars_per_line:]
            draw.text((cond_x, cond_y), line_text, fill="#333", font=font_cond)
            cond_y += 14

        # Ubicación grande (derecha, centrada)
        ubic = data.get("ubicacion", "")
        bbox_loc = draw.textbbox((0, 0), ubic, font=font_big)
        lw = bbox_loc[2] - bbox_loc[0]
        lh = bbox_loc[3] - bbox_loc[1]
        loc_area_w = x1 - half
        draw.text((half + (loc_area_w - lw) // 2, y + (bot_h - lh) // 2), ubic, fill="#333", font=font_big)
        y += bot_h

        # Recortar al alto real
        final_h = y + M
        img = img.crop((0, 0, W, final_h))

        return img

    def _save_as_pdf(self, img, path: str, cantidad: int, Image) -> None:
        """Guarda la(s) etiqueta(s) en formato PDF."""
        pages = [img.copy() for _ in range(cantidad)]
        if len(pages) == 1:
            pages[0].save(path, "PDF", resolution=150)
        else:
            pages[0].save(path, "PDF", resolution=150, save_all=True, append_images=pages[1:])
