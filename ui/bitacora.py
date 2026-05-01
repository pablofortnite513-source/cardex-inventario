import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk
import json

from openpyxl import Workbook

from config.config import BITACORA_FILE, COLORS
from ui.styles import build_header
from utils.data_handler import DataHandler


class BitacoraWindow:
    """Vista de bitácora / auditoría del sistema."""

    MESES = [
        "Todos", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
    ]

    def __init__(self, parent: tk.Tk):
        self.window = tk.Toplevel(parent)
        self.window.title("Bitácora de Auditoría")
        self.window.geometry("1200x520")
        self.window.configure(bg=COLORS["secondary"])

        self.search_var = tk.StringVar()
        self.operacion_var = tk.StringVar(value="Todos")
        self.usuario_var = tk.StringVar(value="Todos")
        self.desde_var = tk.StringVar()
        self.hasta_var = tk.StringVar()
        self.tree: ttk.Treeview | None = None
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

        build_header(wrapper, "Sistema de Gestión  -  Reportes")

        search_row = tk.Frame(wrapper, bg="white")
        search_row.pack(fill="x", pady=(0, 8))

        tk.Entry(search_row, textvariable=self.search_var).pack(side="left", fill="x", expand=True, padx=(0, 8))

        tk.Label(search_row, text="Operación:", bg="white", font=("Segoe UI", 9)).pack(side="left", padx=(8, 2))
        self.operacion_combo = ttk.Combobox(search_row, textvariable=self.operacion_var, state="readonly", width=12)
        self.operacion_combo.pack(side="left", padx=(0, 8))

        tk.Label(search_row, text="Usuario:", bg="white", font=("Segoe UI", 9)).pack(side="left", padx=(0, 2))
        self.usuario_combo = ttk.Combobox(search_row, textvariable=self.usuario_var, state="readonly", width=12)
        self.usuario_combo.pack(side="left", padx=(0, 8))

        tk.Label(search_row, text="Desde:", bg="white", font=("Segoe UI", 9)).pack(side="left", padx=(0, 2))
        tk.Entry(search_row, textvariable=self.desde_var, width=10).pack(side="left", padx=(0, 6))

        tk.Label(search_row, text="Hasta:", bg="white", font=("Segoe UI", 9)).pack(side="left", padx=(0, 2))
        tk.Entry(search_row, textvariable=self.hasta_var, width=10).pack(side="left", padx=(0, 8))

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
            text="Borrar filtros",
            command=self._clear_filters,
            bg=COLORS["border"],
            fg=COLORS["text_dark"],
            relief="flat",
            padx=16,
            pady=5,
        ).pack(side="left", padx=(8, 0))
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
            text="Descargar Excel",
            command=self._download_excel,
            bg=COLORS["primary"],
            fg=COLORS["text_light"],
            relief="flat",
            padx=16,
            pady=5,
        ).pack(side="right")

        columns = (
            "fecha_hora", "usuario", "tipo_operacion",
            "hoja", "id_registro", "detalle",
        )
        self._tree_columns = columns
        # ── Contenedor con scrollbars ──
        tree_frame = tk.Frame(wrapper, bg="white")
        tree_frame.pack(expand=True, fill="both")

        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=16)

        headings = {
            "fecha_hora": "Fecha y Hora",
            "usuario": "Usuario",
            "tipo_operacion": "Tipo Operación",
            "hoja": "Hoja",
            "id_registro": "ID Registro",
            "detalle": "Detalle del Cambio",
        }
        widths = {
            "fecha_hora": 150,
            "usuario": 110,
            "tipo_operacion": 110,
            "hoja": 90,
            "id_registro": 80,
            "detalle": 520,
        }

        for col in columns:
            self.tree.heading(col, text=headings[col], command=lambda c=col: self._sort_column(c, False))
            self.tree.column(col, width=widths[col], minwidth=max(70, int(widths[col] * 0.5)), anchor="w", stretch=True)
        self._tree_base_widths = widths
        self.tree.bind("<Configure>", self._on_tree_resize, add="+")

        v_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        h_scroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")

        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

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

    def _on_tree_resize(self, event: tk.Event) -> None:
        if self.tree is None or not self._tree_columns:
            return
        total_base = sum(self._tree_base_widths.get(col, 1) for col in self._tree_columns)
        if total_base <= 0:
            return
        width = max(event.width - 20, 600)
        for col in self._tree_columns:
            ratio = self._tree_base_widths.get(col, 1) / total_base
            target = int(width * ratio)
            self.tree.column(col, width=max(70, target), stretch=True)

    def _sort_column(self, col: str, reverse: bool) -> None:
        if self.tree is None:
            return
        items = []
        for item_id in self.tree.get_children(""):
            raw = self.tree.set(item_id, col)
            if col in ("id_registro",):
                try:
                    key = float(str(raw).replace(",", ""))
                except ValueError:
                    key = -1.0
            elif col in ("fecha_hora",):
                key = self._parse_datetime(str(raw)) or datetime.min
            else:
                key = str(raw).lower()
            items.append((key, item_id))

        items.sort(reverse=reverse)
        for index, (_key, item_id) in enumerate(items):
            self.tree.move(item_id, "", index)
        self.tree.heading(col, command=lambda: self._sort_column(col, not reverse))

    def _clear_filters(self) -> None:
        """Limpia todos los filtros y muestra todo."""
        self.search_var.set("")
        self.operacion_var.set("Todos")
        self.usuario_var.set("Todos")
        self.desde_var.set("")
        self.hasta_var.set("")
        self.pagina_actual = 1
        self.load_table()

    def _filtered_rows(self) -> list[tuple]:
        query = self.search_var.get().strip().lower()
        op_sel = self.operacion_var.get()
        user_sel = self.usuario_var.get()
        desde = self._parse_datetime(self.desde_var.get())
        hasta = self._parse_datetime(self.hasta_var.get())
        if hasta is not None:
            hasta = hasta.replace(hour=23, minute=59, second=59)

        records = DataHandler.get_all(BITACORA_FILE, "bitacora")
        rows: list[tuple] = []
        for rec in reversed(records):
            fh = rec.get("fecha_hora", "")
            fh_dt = self._parse_datetime(fh)
            if desde is not None and (fh_dt is None or fh_dt < desde):
                continue
            if hasta is not None and (fh_dt is None or fh_dt > hasta):
                continue
            if op_sel != "Todos" and str(rec.get("tipo_operacion", "")).strip() != op_sel:
                continue
            if user_sel != "Todos" and str(rec.get("usuario", "")).strip() != user_sel:
                continue

            detalle = self._build_detail(rec)

            row = (
                fh,
                rec.get("usuario", ""),
                rec.get("tipo_operacion", ""),
                rec.get("hoja", ""),
                rec.get("id_registro", ""),
                detalle,
            )
            if query and query not in str(row).lower():
                continue
            rows.append(row)
        return rows

    def _build_detail(self, rec: dict) -> str:
        campo = str(rec.get("campo", "")).strip()
        v_old = self._format_change_value(rec.get("valor_anterior", ""))
        v_new = self._format_change_value(rec.get("valor_nuevo", ""))
        tipo = str(rec.get("tipo_operacion", "")).strip().lower()

        if tipo in ("entrada", "salida", "inserción", "insercion"):
            if campo and v_new != "-":
                return f"Se creó registro en {campo}: {v_new}"
            return f"Se creó registro: {v_new}"

        if tipo == "anulación" or tipo == "anulacion":
            if v_old != "-" and v_new != "-":
                return f"Se anuló registro. Antes: {v_old}. Resultado: {v_new}"
            return f"Se anuló registro: {v_new}"

        if tipo == "edición" or tipo == "edicion":
            if campo:
                return f"Campo '{campo}' cambió de '{v_old}' a '{v_new}'"
            if v_old != "-" or v_new != "-":
                return f"Se actualizó de '{v_old}' a '{v_new}'"
            return "Se actualizó el registro"

        if campo:
            return f"{campo}: {v_old} -> {v_new}"
        if v_old != "-" or v_new != "-":
            return f"{v_old} -> {v_new}"
        return "Cambio registrado"

    def _available_years(self) -> list[str]:
        # Método mantenido por compatibilidad con llamadas previas.
        records = DataHandler.get_all(BITACORA_FILE, "bitacora")
        years: set[str] = set()
        for rec in records:
            fh = rec.get("fecha_hora", "")
            if len(fh) >= 4:
                years.add(fh[:4])
        current = str(datetime.now().year)
        years.add(current)
        return ["Todos"] + sorted(years)

    @staticmethod
    def _parse_datetime(value: str) -> datetime | None:
        raw = (value or "").strip()
        if not raw:
            return None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                dt = datetime.strptime(raw, fmt)
                if fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
                    dt = dt.replace(hour=0, minute=0, second=0)
                return dt
            except ValueError:
                continue
        return None

    @staticmethod
    def _format_change_value(value: str) -> str:
        text = str(value or "").strip()
        if not text:
            return "-"

        lowered = text.lower()
        if lowered in ("true", "1"):
            return "SI"
        if lowered in ("false", "0"):
            return "NO"

        if " | " in text:
            return " / ".join([p.strip() for p in text.split(" | ") if p.strip()])

        if text.startswith("{") or text.startswith("["):
            try:
                parsed = json.loads(text)
                if isinstance(parsed, dict):
                    return ", ".join([f"{k}: {v}" for k, v in parsed.items()])
                if isinstance(parsed, list):
                    return ", ".join([str(x) for x in parsed])
            except Exception:
                pass

        return text

    def load_table(self) -> None:
        if self.tree is None:
            return

        records = DataHandler.get_all(BITACORA_FILE, "bitacora")

        operaciones = sorted({str(r.get("tipo_operacion", "")).strip() for r in records if str(r.get("tipo_operacion", "")).strip()})
        usuarios = sorted({str(r.get("usuario", "")).strip() for r in records if str(r.get("usuario", "")).strip()})
        self.operacion_combo["values"] = ["Todos"] + operaciones
        self.usuario_combo["values"] = ["Todos"] + usuarios
        if self.operacion_var.get() not in self.operacion_combo["values"]:
            self.operacion_var.set("Todos")
        if self.usuario_var.get() not in self.usuario_combo["values"]:
            self.usuario_var.set("Todos")

        rows = self._filtered_rows()
        try:
            por_pagina = max(1, int(self.por_pagina_var.get().strip()))
        except ValueError:
            por_pagina = 50
            self.por_pagina_var.set("50")

        total = len(rows)
        self.total_paginas = max(1, (total + por_pagina - 1) // por_pagina)
        self.pagina_actual = max(1, min(self.pagina_actual, self.total_paginas))
        start = (self.pagina_actual - 1) * por_pagina
        end = start + por_pagina

        self.tree.delete(*self.tree.get_children())
        for row in rows[start:end]:
            self.tree.insert("", tk.END, values=row)

        if self.pag_label is not None:
            self.pag_label.config(text=f"Página {self.pagina_actual} de {self.total_paginas}")

    def _ir_pagina(self, pagina: int) -> None:
        if pagina < 1 or pagina > self.total_paginas:
            return
        self.pagina_actual = pagina
        self.load_table()

    def _cambiar_por_pagina(self) -> None:
        self.pagina_actual = 1
        self.load_table()

    def _download_excel(self) -> None:
        if self.tree is None:
            return

        rows = [self.tree.item(item, "values") for item in self.tree.get_children()]
        if not rows:
            messagebox.showwarning("Bitácora", "No hay datos para exportar", parent=self.window)
            return

        file_path = filedialog.asksaveasfilename(
            parent=self.window,
            title="Guardar bitácora en Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile=f"bitacora_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        )
        if not file_path:
            return

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Bitacora"

        headers = [
            "Fecha y Hora",
            "Usuario",
            "Tipo Operación",
            "Hoja",
            "ID Registro",
            "Detalle del Cambio",
        ]
        sheet.append(headers)
        for row in rows:
            sheet.append(list(row))

        try:
            workbook.save(file_path)
            messagebox.showinfo("Bitácora", f"Excel generado correctamente:\n{file_path}", parent=self.window)
        except Exception as exc:
            messagebox.showerror("Bitácora", f"No se pudo generar el Excel:\n{exc}", parent=self.window)


def registrar_bitacora(
    usuario: str,
    tipo_operacion: str,
    hoja: str,
    id_registro: str = "",
    campo: str = "",
    valor_anterior: str = "",
    valor_nuevo: str = "",
) -> None:
    """Registra un evento en la bitácora de auditoría."""
    record = {
        "fecha_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "usuario": usuario,
        "tipo_operacion": tipo_operacion,
        "hoja": hoja,
        "id_registro": str(id_registro),
        "campo": campo,
        "valor_anterior": str(valor_anterior),
        "valor_nuevo": str(valor_nuevo),
    }
    DataHandler.add_record(BITACORA_FILE, "bitacora", record)
