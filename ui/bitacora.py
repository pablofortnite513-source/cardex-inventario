import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

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
        self.mes_var = tk.StringVar(value="Todos")
        self.anio_var = tk.StringVar(value="Todos")
        self.tree: ttk.Treeview | None = None

        self._build_ui()
        self.load_table()

    def _build_ui(self) -> None:
        wrapper = tk.Frame(self.window, bg="white", bd=1, relief="solid", padx=12, pady=12)
        wrapper.pack(expand=True, fill="both", padx=14, pady=14)

        build_header(wrapper, "Sistema de Gestión  -  Reportes")

        search_row = tk.Frame(wrapper, bg="white")
        search_row.pack(fill="x", pady=(0, 8))

        tk.Entry(search_row, textvariable=self.search_var).pack(side="left", fill="x", expand=True, padx=(0, 8))

        # Filtro por mes
        tk.Label(search_row, text="Mes:", bg="white", font=("Segoe UI", 9)).pack(side="left", padx=(8, 2))
        ttk.Combobox(
            search_row, textvariable=self.mes_var,
            values=self.MESES, state="readonly", width=12,
        ).pack(side="left", padx=(0, 8))

        # Filtro por año
        tk.Label(search_row, text="Año:", bg="white", font=("Segoe UI", 9)).pack(side="left", padx=(0, 2))
        anios = self._available_years()
        ttk.Combobox(
            search_row, textvariable=self.anio_var,
            values=anios, state="readonly", width=8,
        ).pack(side="left", padx=(0, 8))

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
            "hoja", "id_registro", "campo", "valor_anterior", "valor_nuevo",
        )
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
            "campo": "Campo",
            "valor_anterior": "Valor Anterior",
            "valor_nuevo": "Valor Nuevo",
        }
        widths = {
            "fecha_hora": 150,
            "usuario": 110,
            "tipo_operacion": 110,
            "hoja": 90,
            "id_registro": 80,
            "campo": 120,
            "valor_anterior": 160,
            "valor_nuevo": 160,
        }

        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], minwidth=widths[col], anchor="w")

        v_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        h_scroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")

        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

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

    def _clear_filters(self) -> None:
        """Limpia todos los filtros y muestra todo."""
        self.search_var.set("")
        self.mes_var.set("Todos")
        self.anio_var.set("Todos")
        self.load_table()

    def _available_years(self) -> list[str]:
        records = DataHandler.get_all(BITACORA_FILE, "bitacora")
        years: set[str] = set()
        for rec in records:
            fh = rec.get("fecha_hora", "")
            if len(fh) >= 4:
                years.add(fh[:4])
        current = str(datetime.now().year)
        years.add(current)
        return ["Todos"] + sorted(years)

    def load_table(self) -> None:
        if self.tree is None:
            return

        query = self.search_var.get().strip().lower()
        mes_sel = self.mes_var.get()
        anio_sel = self.anio_var.get()

        # Convertir mes a número
        mes_num = None
        if mes_sel != "Todos":
            try:
                mes_num = self.MESES.index(mes_sel)  # 1-12
            except ValueError:
                pass

        records = DataHandler.get_all(BITACORA_FILE, "bitacora")

        self.tree.delete(*self.tree.get_children())

        for rec in reversed(records):
            # Filtro por año
            fh = rec.get("fecha_hora", "")
            if anio_sel != "Todos" and len(fh) >= 4:
                if fh[:4] != anio_sel:
                    continue

            # Filtro por mes
            if mes_num is not None and len(fh) >= 7:
                try:
                    rec_month = int(fh[5:7])
                    if rec_month != mes_num:
                        continue
                except ValueError:
                    continue

            row = (
                fh,
                rec.get("usuario", ""),
                rec.get("tipo_operacion", ""),
                rec.get("hoja", ""),
                rec.get("id_registro", ""),
                rec.get("campo", ""),
                rec.get("valor_anterior", ""),
                rec.get("valor_nuevo", ""),
            )

            if query and query not in str(row).lower():
                continue

            self.tree.insert("", tk.END, values=row)

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
            "Campo",
            "Valor Anterior",
            "Valor Nuevo",
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
