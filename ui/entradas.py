import tkinter as tk
from datetime import date, datetime
from tkinter import messagebox
from tkinter import ttk

from config.config import (
    COLORS,
    INVENTARIO_FILE,
    PROVEEDORES_FILE,
    SUSTANCIAS_FILE,
    TIPOS_ENTRADA_FILE,
    UBICACIONES_FILE,
    UNIDADES_FILE,
)
from utils.data_handler import DataHandler


class EntryFormWindow:
    """Formulario de entradas con secciones similares al diseno solicitado."""

    def __init__(self, parent: tk.Tk):
        self.window = tk.Toplevel(parent)
        self.window.title("Sistema de Gestion - Entradas")
        self.window.geometry("1240x700")
        self.window.configure(bg=COLORS["secondary"])

        self.catalogs: dict[str, list[dict]] = {}

        self.tipo_entrada_var = tk.StringVar()
        self.fecha_entrada_var = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        self.codigo_var = tk.StringVar()
        self.nombre_var = tk.StringVar()
        self.lote_var = tk.StringVar()

        self.costo_unitario_var = tk.StringVar()
        self.costo_total_var = tk.StringVar(value="0")

        self.cantidad_var = tk.StringVar()
        self.presentacion_var = tk.StringVar()
        self.total_var = tk.StringVar(value="0")
        self.unidad_var = tk.StringVar()
        self.concentracion_var = tk.StringVar()
        self.densidad_var = tk.StringVar()
        self.proveedor_var = tk.StringVar()

        self.certificado_var = tk.BooleanVar(value=False)
        self.msds_var = tk.BooleanVar(value=False)
        self.fecha_venc_var = tk.StringVar()
        self.fecha_doc_var = tk.StringVar()
        self.vigencia_doc_var = tk.StringVar()

        self.ubicacion_var = tk.StringVar()
        self.condicion_var = tk.StringVar()

        self.tipo_combo: ttk.Combobox | None = None
        self.codigo_combo: ttk.Combobox | None = None
        self.unidad_combo: ttk.Combobox | None = None
        self.proveedor_combo: ttk.Combobox | None = None
        self.ubicacion_combo: ttk.Combobox | None = None
        self.observaciones_text: tk.Text | None = None

        self._load_catalogs()
        self._build_ui()
        self._bind_events()

    def _load_catalogs(self) -> None:
        tipos = DataHandler.load_json(TIPOS_ENTRADA_FILE).get("tipos_entrada", [])
        sustancias = DataHandler.load_json(SUSTANCIAS_FILE).get("sustancias", [])
        unidades = DataHandler.load_json(UNIDADES_FILE).get("unidades", [])
        proveedores = DataHandler.load_json(PROVEEDORES_FILE).get("proveedores", [])
        ubicaciones = DataHandler.load_json(UBICACIONES_FILE).get("ubicaciones", [])

        self.catalogs = {
            "tipos": tipos,
            "sustancias": sustancias,
            "unidades": unidades,
            "proveedores": proveedores,
            "ubicaciones": ubicaciones,
        }

    def _build_ui(self) -> None:
        wrapper = tk.Frame(self.window, bg="white", bd=1, relief="solid", padx=14, pady=14)
        wrapper.pack(expand=True, fill="both", padx=14, pady=14)

        tk.Label(
            wrapper,
            text="Sistema de Gestion - Entradas",
            bg=COLORS["primary"],
            fg=COLORS["text_light"],
            font=("Segoe UI", 20, "bold"),
            pady=6,
        ).pack(fill="x", pady=(0, 10))

        top = tk.Frame(wrapper, bg="white")
        top.pack(fill="x", pady=(0, 10))
        top.columnconfigure(0, weight=4)
        top.columnconfigure(1, weight=1)

        general = tk.LabelFrame(top, text="Informacion General", bg="white", fg="#1F4F8A", font=("Segoe UI", 11, "bold"))
        general.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self.tipo_combo = self._add_combo(
            general,
            "Tipo Entrada",
            self.tipo_entrada_var,
            [x.get("nombre", "") for x in self.catalogs["tipos"] if x.get("nombre")],
            0,
            0,
        )
        self._add_entry(general, "Fecha Entrada", self.fecha_entrada_var, 0, 1)
        self.codigo_combo = self._add_combo(
            general,
            "Codigo",
            self.codigo_var,
            self._sustancia_codes(),
            0,
            2,
        )
        self._add_entry(general, "Nombre del Producto", self.nombre_var, 0, 3, readonly=True)
        self._add_entry(general, "Lote", self.lote_var, 0, 4)

        costos = tk.LabelFrame(top, text="Costos", bg="white", fg="#1F4F8A", font=("Segoe UI", 11, "bold"))
        costos.grid(row=0, column=1, sticky="nsew")

        self._add_entry(costos, "Costo Unitario", self.costo_unitario_var, 0, 0)
        self._add_entry(costos, "Costo Total", self.costo_total_var, 0, 1, readonly=True)

        middle = tk.Frame(wrapper, bg="white")
        middle.pack(fill="x", pady=(0, 10))
        middle.columnconfigure(0, weight=3)
        middle.columnconfigure(1, weight=2)

        detalles = tk.LabelFrame(middle, text="Detalles del Producto", bg="white", fg="#1F4F8A", font=("Segoe UI", 11, "bold"))
        detalles.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self._add_entry(detalles, "Cantidad", self.cantidad_var, 0, 0)
        self._add_entry(detalles, "Presentacion", self.presentacion_var, 0, 1)
        self._add_entry(detalles, "Total", self.total_var, 0, 2, readonly=True)
        self.unidad_combo = self._add_combo(
            detalles,
            "Unidad",
            self.unidad_var,
            [x.get("nombre", "") for x in self.catalogs["unidades"] if x.get("nombre")],
            0,
            3,
        )
        self._add_entry(detalles, "Concentracion", self.concentracion_var, 0, 4)
        self._add_entry(detalles, "Densidad (g/mL)", self.densidad_var, 0, 5)
        self.proveedor_combo = self._add_combo(
            detalles,
            "Nombre del Proveedor",
            self.proveedor_var,
            [x.get("nombre", "") for x in self.catalogs["proveedores"] if x.get("nombre")],
            1,
            1,
            col_span=4,
        )

        docs = tk.LabelFrame(middle, text="Documentacion Tecnica", bg="white", fg="#1F4F8A", font=("Segoe UI", 11, "bold"))
        docs.grid(row=0, column=1, sticky="nsew")

        checks = tk.Frame(docs, bg="white")
        checks.pack(fill="x", padx=10, pady=(8, 4))
        tk.Checkbutton(checks, text="Certificado", variable=self.certificado_var, bg="white").pack(side="left", padx=(0, 14))
        tk.Checkbutton(checks, text="MSDS", variable=self.msds_var, bg="white").pack(side="left")

        docs_grid = tk.Frame(docs, bg="white")
        docs_grid.pack(fill="x", padx=10, pady=(0, 10))
        self._add_entry(docs_grid, "Fecha Vencimiento", self.fecha_venc_var, 0, 0)
        self._add_entry(docs_grid, "Fecha Documento", self.fecha_doc_var, 0, 1)
        self._add_entry(docs_grid, "Vigencia Documento", self.vigencia_doc_var, 0, 2, readonly=True)

        storage = tk.LabelFrame(wrapper, text="Almacenamiento y Observaciones", bg="white", fg="#1F4F8A", font=("Segoe UI", 11, "bold"))
        storage.pack(fill="x", pady=(0, 10))

        row_storage = tk.Frame(storage, bg="white")
        row_storage.pack(fill="x", padx=10, pady=10)

        self.ubicacion_combo = self._add_combo(
            row_storage,
            "Ubicacion",
            self.ubicacion_var,
            [x.get("nombre", "") for x in self.catalogs["ubicaciones"] if x.get("nombre")],
            0,
            0,
        )
        self._add_entry(row_storage, "Condicion de Almacenamiento", self.condicion_var, 0, 1)

        obs_frame = tk.Frame(row_storage, bg="white")
        obs_frame.grid(row=0, column=2, sticky="nsew", padx=8)
        tk.Label(obs_frame, text="Observaciones", bg="white").pack(anchor="w")
        self.observaciones_text = tk.Text(obs_frame, height=3)
        self.observaciones_text.pack(fill="x", pady=(4, 0))

        row_storage.columnconfigure(0, weight=1)
        row_storage.columnconfigure(1, weight=2)
        row_storage.columnconfigure(2, weight=3)

        actions = tk.Frame(wrapper, bg="white")
        actions.pack(fill="x")

        tk.Button(
            actions,
            text="Guardar",
            command=self.save,
            bg=COLORS["primary"],
            fg=COLORS["text_light"],
            relief="flat",
            padx=22,
            pady=7,
        ).pack(side="right", padx=(8, 0))
        tk.Button(
            actions,
            text="Limpiar",
            command=self.clear,
            bg=COLORS["primary"],
            fg=COLORS["text_light"],
            relief="flat",
            padx=22,
            pady=7,
        ).pack(side="right", padx=(8, 0))
        tk.Button(
            actions,
            text="Etiquetas",
            command=self.show_label_preview,
            bg="#111111",
            fg="white",
            relief="flat",
            padx=22,
            pady=7,
        ).pack(side="right", padx=(8, 0))
        tk.Button(
            actions,
            text="Salir",
            command=self.window.destroy,
            bg=COLORS["primary"],
            fg=COLORS["text_light"],
            relief="flat",
            padx=22,
            pady=7,
        ).pack(side="right")

    def _add_entry(
        self,
        parent: tk.Widget,
        label: str,
        variable: tk.StringVar,
        row: int,
        col: int,
        readonly: bool = False,
        col_span: int = 1,
    ) -> tk.Entry:
        frame = tk.Frame(parent, bg="white")
        frame.grid(row=row, column=col, columnspan=col_span, padx=8, pady=8, sticky="ew")
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
        row: int,
        col: int,
        col_span: int = 1,
    ) -> ttk.Combobox:
        frame = tk.Frame(parent, bg="white")
        frame.grid(row=row, column=col, columnspan=col_span, padx=8, pady=8, sticky="ew")
        tk.Label(frame, text=label, bg="white").pack(anchor="w")
        combo = ttk.Combobox(frame, textvariable=variable, values=options, state="readonly")
        combo.pack(fill="x", pady=(4, 0))
        parent.columnconfigure(col, weight=1)
        return combo

    def _bind_events(self) -> None:
        if self.codigo_combo is not None:
            self.codigo_combo.bind("<<ComboboxSelected>>", self._on_codigo_selected)
        self.cantidad_var.trace_add("write", lambda *_args: self._recalculate_totals())
        self.costo_unitario_var.trace_add("write", lambda *_args: self._recalculate_totals())
        self.fecha_venc_var.trace_add("write", lambda *_args: self._recalculate_doc_vigencia())

    def _sustancia_codes(self) -> list[str]:
        codes = [str(item.get("codigo", "")).strip() for item in self.catalogs["sustancias"]]
        return sorted([code for code in codes if code])

    def _find_sustancia_by_code(self, code: str) -> dict | None:
        for item in self.catalogs["sustancias"]:
            if str(item.get("codigo", "")).strip() == code:
                return item
        return None

    def _on_codigo_selected(self, _event: tk.Event) -> None:
        selected = self._find_sustancia_by_code(self.codigo_var.get().strip())
        if not selected:
            self.nombre_var.set("")
            return

        self.nombre_var.set(str(selected.get("nombre", "")))
        if not self.concentracion_var.get().strip():
            self.concentracion_var.set(str(selected.get("concentracion", "")))
        if not self.densidad_var.get().strip():
            self.densidad_var.set(str(selected.get("densidad", "")))
        if not self.unidad_var.get().strip():
            self.unidad_var.set(str(selected.get("unidad", "")))

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

    def _to_float(self, value: str) -> float | None:
        clean = (value or "").strip().replace(",", ".")
        if not clean:
            return 0.0
        try:
            return float(clean)
        except ValueError:
            return None

    def _recalculate_doc_vigencia(self) -> None:
        exp = self._parse_date(self.fecha_venc_var.get())
        if exp is None:
            self.vigencia_doc_var.set("")
            return
        self.vigencia_doc_var.set(str((exp - date.today()).days))

    def _recalculate_totals(self) -> None:
        qty = self._to_float(self.cantidad_var.get())
        cost = self._to_float(self.costo_unitario_var.get())

        if qty is None:
            self.total_var.set("-")
            self.costo_total_var.set("-")
            return

        self.total_var.set(str(qty))

        if cost is None:
            self.costo_total_var.set("-")
            return

        self.costo_total_var.set(str(round(qty * cost, 6)))

    def show_label_preview(self) -> None:
        messagebox.showinfo("Etiquetas", "Modulo de etiquetas en construccion")

    def clear(self) -> None:
        self.tipo_entrada_var.set("")
        self.fecha_entrada_var.set(date.today().strftime("%Y-%m-%d"))
        self.codigo_var.set("")
        self.nombre_var.set("")
        self.lote_var.set("")
        self.costo_unitario_var.set("")
        self.costo_total_var.set("0")
        self.cantidad_var.set("")
        self.presentacion_var.set("")
        self.total_var.set("0")
        self.unidad_var.set("")
        self.concentracion_var.set("")
        self.densidad_var.set("")
        self.proveedor_var.set("")
        self.certificado_var.set(False)
        self.msds_var.set(False)
        self.fecha_venc_var.set("")
        self.fecha_doc_var.set("")
        self.vigencia_doc_var.set("")
        self.ubicacion_var.set("")
        self.condicion_var.set("")
        if self.observaciones_text is not None:
            self.observaciones_text.delete("1.0", tk.END)

    def save(self) -> None:
        required = {
            "Tipo Entrada": self.tipo_entrada_var.get().strip(),
            "Fecha Entrada": self.fecha_entrada_var.get().strip(),
            "Codigo": self.codigo_var.get().strip(),
            "Nombre del Producto": self.nombre_var.get().strip(),
            "Cantidad": self.cantidad_var.get().strip(),
            "Unidad": self.unidad_var.get().strip(),
            "Proveedor": self.proveedor_var.get().strip(),
        }
        missing = [k for k, v in required.items() if not v]
        if missing:
            messagebox.showerror("Validacion", f"Completa campos obligatorios: {', '.join(missing)}")
            return

        fecha_entrada = self._parse_date(self.fecha_entrada_var.get())
        if fecha_entrada is None:
            messagebox.showerror("Validacion", "Fecha Entrada no es valida")
            return

        cantidad = self._to_float(self.cantidad_var.get())
        if cantidad is None or cantidad <= 0:
            messagebox.showerror("Validacion", "Cantidad debe ser numerica y mayor a 0")
            return

        observaciones = ""
        if self.observaciones_text is not None:
            observaciones = self.observaciones_text.get("1.0", tk.END).strip()

        record = {
            "tipo_entrada": self.tipo_entrada_var.get().strip(),
            "fecha": self.fecha_entrada_var.get().strip(),
            "codigo": self.codigo_var.get().strip(),
            "nombre": self.nombre_var.get().strip(),
            "lote": self.lote_var.get().strip(),
            "costo_unitario": self.costo_unitario_var.get().strip(),
            "costo_total": self.costo_total_var.get().strip(),
            "cantidad": cantidad,
            "presentacion": self.presentacion_var.get().strip(),
            "total": self.total_var.get().strip(),
            "unidad": self.unidad_var.get().strip(),
            "concentracion": self.concentracion_var.get().strip(),
            "densidad": self.densidad_var.get().strip(),
            "proveedor": self.proveedor_var.get().strip(),
            "certificado": self.certificado_var.get(),
            "msds": self.msds_var.get(),
            "fecha_vencimiento": self.fecha_venc_var.get().strip(),
            "fecha_documento": self.fecha_doc_var.get().strip(),
            "vigencia_documento": self.vigencia_doc_var.get().strip(),
            "ubicacion": self.ubicacion_var.get().strip(),
            "condicion_almacenamiento": self.condicion_var.get().strip(),
            "observaciones": observaciones,
            "stock": cantidad,
        }

        if not DataHandler.add_record(INVENTARIO_FILE, "inventario", record):
            messagebox.showerror("Error", "No se pudo guardar la entrada")
            return

        messagebox.showinfo("Exito", "Entrada registrada en inventario")
        self.clear()
