import tkinter as tk
from datetime import date, datetime
from tkinter import messagebox
from tkinter import ttk

from config.config import COLORS, INVENTARIO_FILE, SALIDAS_FILE, TIPOS_ENTRADA_FILE, UNIDADES_FILE
from utils.data_handler import DataHandler


class SalidasWindow:
    """Formulario de salidas con actualizacion de stock."""

    def __init__(self, parent: tk.Tk):
        self.window = tk.Toplevel(parent)
        self.window.title("Sistema de Gestion - Salidas")
        self.window.geometry("1220x670")
        self.window.configure(bg=COLORS["secondary"])

        self.inventory_data: dict = {}
        self.records: list[dict] = []
        self.selected_index: int | None = None

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
        self.en_uso_var = tk.BooleanVar(value=False)

        self.tipo_combo: ttk.Combobox | None = None
        self.codigo_combo: ttk.Combobox | None = None
        self.lote_combo: ttk.Combobox | None = None
        self.ubicacion_combo: ttk.Combobox | None = None
        self.unidad_combo: ttk.Combobox | None = None
        self.obs_text: tk.Text | None = None

        self._load_data()
        self._build_ui()
        self._bind_events()

    def _load_data(self) -> None:
        self.inventory_data = DataHandler.load_json(INVENTARIO_FILE)
        self.records = self.inventory_data.get("inventario", [])

        tipos_data = DataHandler.load_json(TIPOS_ENTRADA_FILE)
        self.tipo_salida_options = [x.get("nombre", "") for x in tipos_data.get("tipos_entrada", []) if x.get("nombre")]
        if not self.tipo_salida_options:
            self.tipo_salida_options = ["Consumo", "Transferencia", "Ajuste", "Merma", "Prestamo"]

        unidades_data = DataHandler.load_json(UNIDADES_FILE)
        self.unidad_options = [x.get("nombre", "") for x in unidades_data.get("unidades", []) if x.get("nombre")]

    def _build_ui(self) -> None:
        wrapper = tk.Frame(self.window, bg="white", bd=1, relief="solid", padx=14, pady=14)
        wrapper.pack(expand=True, fill="both", padx=14, pady=14)

        tk.Label(
            wrapper,
            text="Sistema de Gestion - Salidas",
            bg=COLORS["primary"],
            fg=COLORS["text_light"],
            font=("Segoe UI", 18, "bold"),
            pady=6,
        ).pack(fill="x", pady=(0, 10))

        general = tk.LabelFrame(wrapper, text="Informacion General", bg="white", fg="#1F4F8A", font=("Segoe UI", 11, "bold"))
        general.pack(fill="x", padx=4, pady=(0, 10))

        row1 = tk.Frame(general, bg="white")
        row1.pack(fill="x", padx=10, pady=10)

        self.tipo_combo = self._add_combo(row1, "Tipo Salida", self.tipo_salida_var, self.tipo_salida_options, 0)
        self._add_entry(row1, "Fecha Salida", self.fecha_salida_var, 1)
        self.codigo_combo = self._add_combo(row1, "Codigo", self.codigo_var, self._available_codes(), 2)
        self._add_entry(row1, "Nombre del Producto", self.nombre_var, 3, readonly=True)
        self.lote_combo = self._add_combo(row1, "Lote", self.lote_var, [], 4)
        self.ubicacion_combo = self._add_combo(row1, "Ubicacion Origen", self.ubicacion_var, [], 5)

        vigencia = tk.LabelFrame(wrapper, text="Vigencia y Stock", bg="white", fg="#1F4F8A", font=("Segoe UI", 11, "bold"))
        vigencia.pack(fill="x", padx=4, pady=(0, 10))

        row2 = tk.Frame(vigencia, bg="white")
        row2.pack(fill="x", padx=10, pady=10)
        self._add_entry(row2, "Vigencia", self.vigencia_var, 0, readonly=True)
        self._add_entry(row2, "Dias Vigencia", self.dias_vigencia_var, 1, readonly=True)
        self._add_entry(row2, "Stock", self.stock_actual_var, 2, readonly=True)
        self._add_entry(row2, "Nueva Stock", self.nuevo_stock_var, 3, readonly=True)
        self._add_entry(row2, "Unidad", self.unidad_stock_var, 4, readonly=True)

        detalles = tk.LabelFrame(wrapper, text="Detalles del Producto", bg="white", fg="#1F4F8A", font=("Segoe UI", 11, "bold"))
        detalles.pack(fill="x", padx=4, pady=(0, 10))

        row3 = tk.Frame(detalles, bg="white")
        row3.pack(fill="x", padx=10, pady=10)
        self._add_entry(row3, "Cantidad", self.cantidad_var, 0)
        self.unidad_combo = self._add_combo(row3, "Unidad", self.unidad_var, self.unidad_options, 1)
        self._add_entry(row3, "Densidad (g/mL)", self.densidad_var, 2)
        self._add_entry(row3, "Peso Inicial", self.peso_inicial_var, 3)
        self._add_entry(row3, "Peso Final", self.peso_final_var, 4)
        tk.Checkbutton(row3, text="Liquido", variable=self.liquido_var, bg="white").grid(row=0, column=5, padx=8, sticky="w")

        obs = tk.LabelFrame(wrapper, text="Observaciones de Salida", bg="white", fg="#1F4F8A", font=("Segoe UI", 11, "bold"))
        obs.pack(fill="x", padx=4, pady=(0, 10))

        row4 = tk.Frame(obs, bg="white")
        row4.pack(fill="x", padx=10, pady=10)

        tk.Label(row4, text="Observaciones", bg="white").grid(row=0, column=0, sticky="w")
        self.obs_text = tk.Text(row4, height=3, width=72)
        self.obs_text.grid(row=1, column=0, padx=(0, 10), sticky="ew")
        tk.Checkbutton(row4, text="En uso", variable=self.en_uso_var, bg="white", font=("Segoe UI", 10, "bold")).grid(
            row=1,
            column=1,
            sticky="w",
        )
        row4.columnconfigure(0, weight=1)

        actions = tk.Frame(wrapper, bg="white")
        actions.pack(fill="x")

        tk.Button(
            actions,
            text="Guardar",
            command=self.save,
            bg=COLORS["primary"],
            fg=COLORS["text_light"],
            relief="flat",
            padx=28,
            pady=7,
        ).pack(side="right", padx=(8, 0))
        tk.Button(
            actions,
            text="Salir",
            command=self.window.destroy,
            bg=COLORS["primary"],
            fg=COLORS["text_light"],
            relief="flat",
            padx=28,
            pady=7,
        ).pack(side="right")

    def _add_entry(
        self,
        parent: tk.Widget,
        label: str,
        variable: tk.StringVar,
        col: int,
        readonly: bool = False,
    ) -> tk.Entry:
        frame = tk.Frame(parent, bg="white")
        frame.grid(row=0, column=col, padx=8, sticky="ew")
        tk.Label(frame, text=label, bg="white").pack(anchor="w")
        state = "readonly" if readonly else "normal"
        entry = tk.Entry(frame, textvariable=variable, state=state)
        entry.pack(fill="x", pady=(4, 0))
        parent.columnconfigure(col, weight=1)
        return entry

    def _add_combo(
        self,
        parent: tk.Widget,
        label: str,
        variable: tk.StringVar,
        options: list[str],
        col: int,
    ) -> ttk.Combobox:
        frame = tk.Frame(parent, bg="white")
        frame.grid(row=0, column=col, padx=8, sticky="ew")
        tk.Label(frame, text=label, bg="white").pack(anchor="w")
        combo = ttk.Combobox(frame, textvariable=variable, values=options, state="readonly")
        combo.pack(fill="x", pady=(4, 0))
        parent.columnconfigure(col, weight=1)
        return combo

    def _bind_events(self) -> None:
        self.cantidad_var.trace_add("write", lambda *_args: self._recalculate_new_stock())
        if self.codigo_combo is not None:
            self.codigo_combo.bind("<<ComboboxSelected>>", self._on_code_selected)
        if self.lote_combo is not None:
            self.lote_combo.bind("<<ComboboxSelected>>", self._on_lote_selected)
        if self.ubicacion_combo is not None:
            self.ubicacion_combo.bind("<<ComboboxSelected>>", self._on_location_selected)

    def _available_codes(self) -> list[str]:
        codes = {str(record.get("codigo", "")).strip() for record in self.records if str(record.get("codigo", "")).strip()}
        return sorted(codes)

    def _records_for_code(self, code: str) -> list[tuple[int, dict]]:
        rows: list[tuple[int, dict]] = []
        for idx, record in enumerate(self.records):
            if str(record.get("codigo", "")).strip() == code:
                rows.append((idx, record))
        return rows

    def _selected_record(self) -> dict | None:
        if self.selected_index is None:
            return None
        if self.selected_index < 0 or self.selected_index >= len(self.records):
            return None
        return self.records[self.selected_index]

    def _to_float(self, value: str) -> float | None:
        clean = (value or "").strip().replace(",", ".")
        if not clean:
            return 0.0
        try:
            return float(clean)
        except ValueError:
            return None

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

    def _extract_expiration(self, record: dict) -> date | None:
        for key in ["fecha_vencimiento", "f_vencimiento", "vencimiento", "fecha_venc", "fecha_vence"]:
            parsed = self._parse_date(str(record.get(key, "")))
            if parsed:
                return parsed
        return None

    def _update_stock_block(self, record: dict) -> None:
        stock = record.get("stock", record.get("cantidad", 0))
        try:
            stock_value = float(stock)
        except (TypeError, ValueError):
            stock_value = 0.0

        self.stock_actual_var.set(str(stock_value))
        self.unidad_stock_var.set(str(record.get("unidad", "")))
        if not self.unidad_var.get().strip():
            self.unidad_var.set(str(record.get("unidad", "")))

        exp = self._extract_expiration(record)
        if exp is None:
            self.vigencia_var.set("SIN FECHA")
            self.dias_vigencia_var.set("")
        else:
            days = (exp - date.today()).days
            self.vigencia_var.set(exp.strftime("%Y-%m-%d"))
            self.dias_vigencia_var.set(str(days))

        self._recalculate_new_stock()

    def _on_code_selected(self, _event: tk.Event) -> None:
        code = self.codigo_var.get().strip()
        matches = self._records_for_code(code)
        if not matches:
            self.selected_index = None
            self.nombre_var.set("")
            self.lote_var.set("")
            self.ubicacion_var.set("")
            if self.lote_combo is not None:
                self.lote_combo["values"] = []
            if self.ubicacion_combo is not None:
                self.ubicacion_combo["values"] = []
            self.stock_actual_var.set("0")
            self.nuevo_stock_var.set("0")
            return

        self.nombre_var.set(str(matches[0][1].get("nombre", "")))
        lotes = sorted({str(record.get("lote", "")).strip() for _, record in matches if str(record.get("lote", "")).strip()})
        if self.lote_combo is not None:
            self.lote_combo["values"] = lotes

        if lotes:
            self.lote_var.set(lotes[0])
            self._on_lote_selected(None)
        else:
            self.selected_index = matches[0][0]
            record = matches[0][1]
            self.ubicacion_var.set(str(record.get("ubicacion", "")))
            if self.ubicacion_combo is not None:
                self.ubicacion_combo["values"] = [self.ubicacion_var.get()]
            self._update_stock_block(record)

    def _on_lote_selected(self, _event: tk.Event | None) -> None:
        code = self.codigo_var.get().strip()
        lote = self.lote_var.get().strip()
        matches = self._records_for_code(code)

        if not matches:
            return

        filtered = [(idx, rec) for idx, rec in matches if str(rec.get("lote", "")).strip() == lote]
        picked = filtered[0] if filtered else matches[0]

        self.selected_index = picked[0]
        record = picked[1]

        ubicacion = str(record.get("ubicacion", ""))
        self.ubicacion_var.set(ubicacion)
        if self.ubicacion_combo is not None:
            self.ubicacion_combo["values"] = [ubicacion] if ubicacion else []

        self._update_stock_block(record)

    def _on_location_selected(self, _event: tk.Event | None) -> None:
        code = self.codigo_var.get().strip()
        lote = self.lote_var.get().strip()
        ubicacion = self.ubicacion_var.get().strip()
        matches = self._records_for_code(code)

        for idx, record in matches:
            if str(record.get("lote", "")).strip() == lote and str(record.get("ubicacion", "")).strip() == ubicacion:
                self.selected_index = idx
                self._update_stock_block(record)
                return

    def _recalculate_new_stock(self) -> None:
        record = self._selected_record()
        if record is None:
            self.nuevo_stock_var.set("0")
            return

        stock = self._to_float(str(record.get("stock", record.get("cantidad", 0))))
        qty = self._to_float(self.cantidad_var.get())

        if stock is None:
            stock = 0.0
        if qty is None:
            self.nuevo_stock_var.set("-")
            return

        self.nuevo_stock_var.set(str(stock - qty))

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
            messagebox.showerror("Validacion", f"Completa campos obligatorios: {', '.join(missing)}")
            return

        salida_date = self._parse_date(self.fecha_salida_var.get())
        if salida_date is None:
            messagebox.showerror("Validacion", "Fecha Salida no es valida")
            return

        cantidad = self._to_float(self.cantidad_var.get())
        if cantidad is None or cantidad <= 0:
            messagebox.showerror("Validacion", "Cantidad debe ser numerica y mayor a 0")
            return

        record = self._selected_record()
        if record is None:
            messagebox.showerror("Validacion", "Selecciona un producto valido")
            return

        current_stock = self._to_float(str(record.get("stock", record.get("cantidad", 0))))
        if current_stock is None:
            current_stock = 0.0

        if cantidad > current_stock:
            messagebox.showerror("Stock", "La cantidad de salida no puede superar el stock disponible")
            return

        new_stock = round(current_stock - cantidad, 6)
        self.records[self.selected_index]["stock"] = new_stock

        if not DataHandler.save_json(INVENTARIO_FILE, self.inventory_data):
            messagebox.showerror("Error", "No se pudo actualizar el stock en inventario")
            return

        observaciones = ""
        if self.obs_text is not None:
            observaciones = self.obs_text.get("1.0", tk.END).strip()

        salida_record = {
            "fecha_salida": self.fecha_salida_var.get().strip(),
            "tipo_salida": self.tipo_salida_var.get().strip(),
            "codigo": self.codigo_var.get().strip(),
            "nombre": self.nombre_var.get().strip(),
            "lote": self.lote_var.get().strip(),
            "ubicacion_origen": self.ubicacion_var.get().strip(),
            "cantidad": cantidad,
            "unidad": self.unidad_var.get().strip() or self.unidad_stock_var.get().strip(),
            "densidad": self.densidad_var.get().strip(),
            "peso_inicial": self.peso_inicial_var.get().strip(),
            "peso_final": self.peso_final_var.get().strip(),
            "liquido": self.liquido_var.get(),
            "en_uso": self.en_uso_var.get(),
            "observaciones": observaciones,
            "stock_anterior": current_stock,
            "stock_nuevo": new_stock,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        if not DataHandler.add_record(SALIDAS_FILE, "salidas", salida_record):
            messagebox.showwarning("Aviso", "Salida guardada, pero no se pudo registrar el historico")

        messagebox.showinfo("Exito", "Salida registrada y stock actualizado")
        self._reset_form()

    def _reset_form(self) -> None:
        self._load_data()
        self.selected_index = None

        self.tipo_salida_var.set("")
        self.fecha_salida_var.set(date.today().strftime("%Y-%m-%d"))
        self.codigo_var.set("")
        self.nombre_var.set("")
        self.lote_var.set("")
        self.ubicacion_var.set("")
        self.vigencia_var.set("")
        self.dias_vigencia_var.set("")
        self.stock_actual_var.set("0")
        self.nuevo_stock_var.set("0")
        self.unidad_stock_var.set("")

        self.cantidad_var.set("")
        self.unidad_var.set("")
        self.densidad_var.set("")
        self.peso_inicial_var.set("")
        self.peso_final_var.set("")
        self.liquido_var.set(False)
        self.en_uso_var.set(False)

        if self.obs_text is not None:
            self.obs_text.delete("1.0", tk.END)

        if self.codigo_combo is not None:
            self.codigo_combo["values"] = self._available_codes()
        if self.lote_combo is not None:
            self.lote_combo["values"] = []
        if self.ubicacion_combo is not None:
            self.ubicacion_combo["values"] = []
        if self.unidad_combo is not None:
            self.unidad_combo["values"] = self.unidad_options
        if self.tipo_combo is not None:
            self.tipo_combo["values"] = self.tipo_salida_options