import importlib
import tkinter as tk
from datetime import date, datetime

from config.config import (
    ALMACENES_FILE,
    CONDICIONES_FILE,
    ENTRADAS_FILE,
    IMAGES_PATH,
    PROVEEDORES_FILE,
    SALIDAS_FILE,
    SUSTANCIAS_FILE,
    TIPOS_ENTRADA_FILE,
    TIPOS_SALIDA_FILE,
    UBICACIONES_FILE,
    UNIDADES_FILE,
)
from config.config import COLORS
from ui.bitacora import BitacoraWindow
from ui.checklist import CheckListWindow
from ui.entradas import EntryFormWindow
from ui.maestras import LocationMasterWindow, MasterCatalogWindow, SubstanceMasterWindow
from ui.reportes import ReportesWindow
from ui.salidas import SalidasWindow
from ui.stock_analista import StockAnalistaWindow
from ui.stock import StockWindow
from ui.users import CreateUserWindow
from ui.vigencias import VigenciasWindow
from utils.data_handler import DataHandler


class MainMenuWindow:
    """Menu principal del sistema."""

    def __init__(self, root: tk.Tk, user: dict):
        self.root = root
        self.user = user
        self.user_role = str(self.user.get("rol", "")).strip().lower()
        self.user_perms = self.user.get("permisos", {}) if isinstance(self.user.get("permisos", {}), dict) else {}
        self.main_image_tk = None
        self.button_images = {}
        self._open_windows: list[tk.Toplevel] = []
        self.notify_container: tk.Frame | None = None
        self._notifications_expanded = False
        self._cached_notifications: list[str] = []
        self._build_ui()
        self._check_notifications()

    def _build_ui(self) -> None:
        self.root.configure(bg=COLORS["secondary"])
        self._set_balanced_geometry()

        wrapper = tk.Frame(self.root, bg="white", bd=1, relief="solid", padx=14, pady=12)
        wrapper.pack(expand=True, fill="both")

        # ── Header: barra rosa con título + logo ──
        header = tk.Frame(wrapper, bg=COLORS["primary"])
        header.pack(fill="x", pady=(0, 8))

        tk.Label(
            header,
            text="Sistema de Gestión  -  Menú Principal",
            bg=COLORS["primary"],
            fg="white",
            font=("Segoe UI", 18, "bold"),
            padx=14,
            pady=8,
        ).pack(side="left", fill="x", expand=True)

        self._place_header_logo(header, height=80)

        # ── Info usuario + Login ──
        info_row = tk.Frame(wrapper, bg="white")
        info_row.pack(fill="x", pady=(0, 8))

        tk.Label(
            info_row,
            text=f"Usuario: {self.user.get('nombre', 'N/A')} ({self.user.get('rol', 'N/A')})",
            bg="white",
            fg=COLORS["text_dark"],
            font=("Segoe UI", 10),
        ).pack(side="left")

        tk.Button(
            info_row,
            text="Salir",
            command=self.root.destroy,
            bg=COLORS["error"],
            fg=COLORS["text_light"],
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=16,
            pady=3,
        ).pack(side="right")

        tk.Button(
            info_row,
            text="Cerrar sesión",
            command=self._logout,
            bg=COLORS["primary"],
            fg=COLORS["text_light"],
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=16,
            pady=3,
        ).pack(side="right", padx=(0, 8))

        notify_frame = tk.Frame(wrapper, bg="#FFF8E1", bd=1, relief="solid", padx=10, pady=5)
        notify_frame.pack(fill="x", pady=(0, 8))

        tk.Label(
            notify_frame,
            text="⚠️ NOTIFICACIONES",
            bg="#FFF8E1",
            fg="#E65100",
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w")

        self.notify_container = tk.Frame(notify_frame, bg="#FFF8E1")
        self.notify_container.pack(fill="x", pady=(2, 0))

        # ── Body: imagen + paneles ──
        body = tk.Frame(wrapper, bg="white")
        body.pack(expand=True, fill="both")

        media_col = tk.LabelFrame(
            body, text="", bg="white", fg=COLORS["text_dark"],
            font=("Segoe UI", 11, "bold"), bd=1,
        )
        media_col.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(4, 0))

        image_placeholder = tk.Frame(media_col, bg="#ECEFF4", bd=1, relief="solid")
        image_placeholder.pack(expand=True, fill="both", padx=8, pady=8)
        self._render_main_image(image_placeholder)

        moves_col = tk.LabelFrame(
            body, text="Movimientos y Reportes", bg="white", fg=COLORS["text_dark"],
            font=("Segoe UI", 11, "bold"), bd=1,
        )
        moves_col.grid(row=0, column=1, sticky="nsew", padx=6, pady=(4, 0))

        masters_col = tk.LabelFrame(
            body, text="Maestras", bg="white", fg=COLORS["text_dark"],
            font=("Segoe UI", 11, "bold"), bd=1,
        )
        masters_col.grid(row=0, column=2, sticky="nsew", padx=(6, 0), pady=(4, 0))

        self._create_panel_buttons(
            moves_col,
            [
                ("Entradas", self.open_entradas, "entradas"),
                ("Salidas", self.open_salidas, "salidas"),
                ("Vigencia", self.open_vigencias, "vigencias"),
                ("Stock", self.open_stock, "stock"),
                ("Stock Analista", self.open_stock_analista, "stock"),
                ("Bitacora", self.open_bitacora, "auditoria"),
                ("Reportes", self.open_reportes, "auditoria"),
            ],
        )
        self._create_panel_buttons(
            masters_col,
            [
                ("Sustancias", self.open_sustancias, "inventario"),
                ("T. Entrada", self.open_tipo_entrada, "inventario"),
                ("T. Salida", self.open_tipo_salida, "inventario"),
                ("Proveedor", self.open_proveedor, "inventario"),
                ("Usuarios", self.open_usuarios, "usuarios_admin"),
                ("C. Almace", self.open_almacen, "inventario"),
                ("Cond. Almac.", self.open_condicion_almac, "inventario"),
                ("Unidad", self.open_unidad, "inventario"),
                ("Ubicacion", self.open_ubicacion, "inventario"),
            ],
        )

        body.columnconfigure(0, weight=14)
        body.columnconfigure(1, weight=17)
        body.columnconfigure(2, weight=17)
        body.rowconfigure(0, weight=1)
        

    def _set_balanced_geometry(self) -> None:
        """Ajusta la ventana a un tamano comodo segun la resolucion actual."""
        self.root.update_idletasks()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()

        width = min(max(int(screen_w * 0.88), 1120), 1380)
        height = min(max(int(screen_h * 0.84), 640), 860)

        pos_x = max((screen_w - width) // 2, 0)
        pos_y = max((screen_h - height) // 2, 0)
        self.root.geometry(f"{width}x{height}+{pos_x}+{pos_y}")

    def _render_main_image(self, parent: tk.Frame) -> None:
        image_path = IMAGES_PATH / "imagenppal.jpg"

        if image_path.exists():
            try:
                image_mod = importlib.import_module("PIL.Image")
                image_tk_mod = importlib.import_module("PIL.ImageTk")

                img = image_mod.open(image_path)
                resampling = getattr(image_mod, "Resampling", None)
                method = resampling.LANCZOS if resampling else image_mod.LANCZOS
                img.thumbnail((600, 350), method)
                self.main_image_tk = image_tk_mod.PhotoImage(img)
                tk.Label(parent, image=self.main_image_tk, bg="#ECEFF4").pack(expand=True, fill="both", padx=8, pady=8)
                return
            except Exception:
                pass

        tk.Label(
            parent,
            text="No se pudo cargar la imagen principal",
            bg="#ECEFF4",
            fg="#6C7887",
            font=("Segoe UI", 13, "bold"),
            justify="center",
        ).pack(expand=True)
        tk.Label(
            parent,
            text=f"Ruta esperada: {image_path}",
            bg="#ECEFF4",
            fg="#6C7887",
            font=("Segoe UI", 9),
        ).pack(pady=(0, 12))

    def _place_header_logo(self, parent: tk.Frame, height: int = 50) -> None:
        """Coloca el logo de CECIF en el header (lado derecho)."""
        logo_path = IMAGES_PATH / "imgLogocecif.png"
        if not logo_path.exists():
            return
        try:
            image_mod = importlib.import_module("PIL.Image")
            image_tk_mod = importlib.import_module("PIL.ImageTk")
            img = image_mod.open(logo_path)
            ratio = height / img.height
            new_w = int(img.width * ratio)
            resampling = getattr(image_mod, "Resampling", None)
            method = resampling.LANCZOS if resampling else image_mod.LANCZOS
            img = img.resize((new_w, height), method)
            self.header_logo_tk = image_tk_mod.PhotoImage(img)
            tk.Label(parent, image=self.header_logo_tk, bg=COLORS["primary"]).pack(
                side="right", padx=(8, 12), pady=4,
            )
        except Exception:
            pass

    def _get_button_image_path(self, label: str) -> str | None:
        """Mapea nombre de botón a archivo de imagen."""
        mapping = {
            "Entradas": "imgEntrada.png",
            "Salidas": "imgSalida.png",
            "Vigencia": "imgVigencia.png",
            "Stock": "imgStock.png",
            "Stock Analista": "imgReporte.png",
            "Usuarios": "imgUsuario.png",
            "Bitacora": "imgReporte.png",
            "Reportes": "imgReporte.png",
            "Sustancias": "imgSustancia.png",
            "T. Entrada": "imgTentrada.png",
            "T. Salida": "imgTentrada.png",
            "Proveedor": "imgProveedor.png",
            "C. Almace": "imgCalmacen.png",
            "Unidad": "imgUnidad.png",
            "Ubicacion": "imgUbicacion.png",
            "Cond. Almac.": "imgCalmacen.png",
        }
        return mapping.get(label)

    def _load_button_icon(self, filename: str) -> object | None:
        """Carga un icono desde la carpeta Imagenes."""
        image_path = IMAGES_PATH / filename
        if not image_path.exists():
            return None

        try:
            image_mod = importlib.import_module("PIL.Image")
            image_tk_mod = importlib.import_module("PIL.ImageTk")
            img = image_mod.open(image_path)
            img.thumbnail((45, 55), image_mod.LANCZOS if hasattr(image_mod, "LANCZOS") else 1)
            return image_tk_mod.PhotoImage(img)
        except Exception:
            return None

    def _create_panel_buttons(self, parent: tk.Widget, buttons: list[tuple[str, object, str]]) -> None:
        grid = tk.Frame(parent, bg="white")
        grid.pack(fill="x", padx=6, pady=6)

        for idx, (label, callback, perm_key) in enumerate(buttons):
            row = idx // 2
            col = idx % 2
            has_access = self._has_permission(perm_key)

            cmd = self._build_permission_command(label, perm_key, callback)
            fg = COLORS["text_dark"] if has_access else "#5A5A5A"
            bg = "white" if has_access else "#F1F1F1"

            # Cargar icono
            icon_tk = None
            img_filename = self._get_button_image_path(label)
            if img_filename:
                icon_tk = self._load_button_icon(img_filename)
                if icon_tk:
                    self.button_images[label] = icon_tk

            # Botón único con imagen + texto — toda la celda es clickeable
            btn = tk.Button(
                grid,
                text=f"  {label}",
                image=icon_tk if icon_tk else "",
                compound="left" if icon_tk else "none",
                command=cmd,
                bg=bg,
                fg=fg,
                relief="solid",
                bd=1,
                activebackground="#F5F5F5",
                activeforeground=COLORS["text_dark"],
                font=("Segoe UI", 11),
                anchor="w",
                padx=8,
                pady=3,
                state="normal",
                disabledforeground="#5A5A5A",
            )
            btn.grid(row=row, column=col, padx=6, pady=8, sticky="nsew")

        max_rows = (len(buttons) + 1) // 2
        for r in range(max_rows):
            grid.rowconfigure(r, weight=0)
        for c in range(2):
            grid.columnconfigure(c, weight=1)
        # 🔥 Línea justo debajo del último botón
        separator = tk.Frame(grid, bg="#D0D0D0", height=1)
        separator.grid(row=max_rows, column=0, columnspan=2, sticky="ew", pady=(6, 0))

    def _has_permission(self, perm_key: str) -> bool:
        if perm_key in {"inventario", "usuarios_admin"}:
            return self.user_role == "admin"
        if self.user_role == "admin":
            return True
        return bool(self.user_perms.get(perm_key, False))

    def _build_permission_command(self, module_label: str, perm_key: str, callback):
        def _command() -> None:
            if not self._has_permission(perm_key):
                self._no_access(module_label)
                return
            callback()

        return _command

    def _can_open_window(self) -> bool:
        """Limita a 3 ventanas Toplevel abiertas simultáneamente."""
        self._open_windows = [w for w in self._open_windows if w.winfo_exists()]
        if len(self._open_windows) >= 3:
            import tkinter.messagebox as mb
            mb.showwarning("Límite", "Ya tienes 3 ventanas abiertas. Cierra alguna para abrir otra.", parent=self.root)
            return False
        return True

    def _track_window(self, obj) -> None:
        """Registra la ventana Toplevel del objeto abierto."""
        win = getattr(obj, "window", None)
        if win is not None:
            self._open_windows.append(win)

    def _guard_access(self, perm_key: str, module_label: str) -> bool:
        if not self._has_permission(perm_key):
            self._no_access(module_label)
            return False
        return True

    @staticmethod
    def _safe_float(value) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _parse_date(value: str) -> date | None:
        raw = (value or "").strip()
        if not raw:
            return None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                continue
        return None

    def _check_notifications(self) -> None:
        """Verifica y muestra notificaciones de vencimientos y stock bajo."""
        if self.notify_container is None or not self.notify_container.winfo_exists():
            return

        notifications: list[str] = []
        today = date.today()

        entradas = [r for r in DataHandler.get_all(ENTRADAS_FILE, "entradas") if not r.get("anulado")]
        salidas = [r for r in DataHandler.get_all(SALIDAS_FILE, "salidas") if not r.get("anulado")]
        sustancias = DataHandler.load_json(SUSTANCIAS_FILE).get("maestrasSustancias", [])

        sust_by_id = {s.get("id"): s for s in sustancias if s.get("id") is not None}

        stock_lote: dict[tuple[object, str], float] = {}
        for r in entradas:
            key = (r.get("id_sustancia"), str(r.get("lote", "")).strip())
            stock_lote[key] = stock_lote.get(key, 0.0) + self._safe_float(r.get("total", 0))
        for r in salidas:
            key = (r.get("id_sustancia"), str(r.get("lote", "")).strip())
            stock_lote[key] = stock_lote.get(key, 0.0) - self._safe_float(r.get("cantidad", 0))

        # 1) Vencidos y 2) Por vencer
        for r in entradas:
            sid = r.get("id_sustancia")
            lote = str(r.get("lote", "")).strip()
            if not lote:
                continue
            stock_actual = stock_lote.get((sid, lote), 0.0)
            if stock_actual <= 0:
                continue

            fv = self._parse_date(r.get("fecha_vencimiento", ""))
            if fv is None:
                continue
            dias = (fv - today).days
            nombre = str(sust_by_id.get(sid, {}).get("nombre", f"ID {sid}"))

            if dias < 0:
                notifications.append(f"{nombre} - Lote {lote} - Vencido hace {abs(dias)} días")
            elif dias <= 30:
                notifications.append(f"{nombre} - Lote {lote} - Vence en {dias} días")

        # 3) Stock bajo por sustancia
        stock_por_sustancia: dict[object, float] = {}
        for (sid, _lote), stk in stock_lote.items():
            stock_por_sustancia[sid] = stock_por_sustancia.get(sid, 0.0) + stk

        for sid, stock in stock_por_sustancia.items():
            sust = sust_by_id.get(sid, {})
            minimo = self._safe_float(sust.get("cantidad_minima_stock", sust.get("cantidad_minima", 0)))
            if minimo > 0 and stock < minimo:
                nombre = str(sust.get("nombre", f"ID {sid}"))
                notifications.append(f"{nombre} - Stock: {round(stock, 2)} / Mínimo: {round(minimo, 2)}")

        self._cached_notifications = notifications
        self._render_notifications()

        self.root.after(1800000, self._check_notifications)

    def _render_notifications(self) -> None:
        if self.notify_container is None or not self.notify_container.winfo_exists():
            return

        for widget in self.notify_container.winfo_children():
            widget.destroy()

        notifications = self._cached_notifications

        if not notifications:
            tk.Label(
                self.notify_container,
                text="✓ Todo en orden",
                bg="#FFF8E1",
                fg="#2E7D32",
                font=("Segoe UI", 9),
            ).pack(anchor="w")
        else:
            visible_count = len(notifications) if self._notifications_expanded else min(3, len(notifications))
            for notif in notifications[:visible_count]:
                tk.Label(
                    self.notify_container,
                    text=f"• {notif}",
                    bg="#FFF8E1",
                    fg="#D32F2F",
                    font=("Segoe UI", 9),
                    wraplength=600,
                    justify="left",
                ).pack(anchor="w")

            if len(notifications) > 3:
                if not self._notifications_expanded:
                    tk.Label(
                        self.notify_container,
                        text=f"... y {len(notifications) - 3} más",
                        bg="#FFF8E1",
                        fg="#666",
                        font=("Segoe UI", 9, "italic"),
                    ).pack(anchor="w")

                tk.Button(
                    self.notify_container,
                    text="Ver menos ▲" if self._notifications_expanded else "Ver más ▼",
                    command=self._toggle_notifications,
                    bg="#FFF8E1",
                    fg="#1F4F8A",
                    relief="flat",
                    cursor="hand2",
                    padx=0,
                    pady=0,
                    font=("Segoe UI", 9, "bold"),
                    activebackground="#FFF8E1",
                    activeforeground="#1F4F8A",
                ).pack(anchor="w", pady=(2, 0))

    def _toggle_notifications(self) -> None:
        self._notifications_expanded = not self._notifications_expanded
        self._render_notifications()

    def open_entradas(self) -> None:
        if not self._guard_access("entradas", "Entradas"):
            return
        if not self._can_open_window():
            return
        import tkinter.messagebox as mb

        do_checklist = mb.askyesno(
            "Lista de Chequeo",
            "¿Desea realizar lista de chequeo?",
            parent=self.root,
        )

        if do_checklist:
            def _on_checklist_saved(prefill: dict) -> None:
                ew = EntryFormWindow(
                    self.root,
                    usuario=self.user.get("nombre", ""),
                    rol=self.user.get("rol", ""),
                    prefill=prefill,
                )
                self._track_window(ew)

            w = CheckListWindow(self.root, usuario=self.user.get("nombre", ""), on_saved=_on_checklist_saved)
        else:
            w = EntryFormWindow(self.root, usuario=self.user.get("nombre", ""), rol=self.user.get("rol", ""))
        self._track_window(w)

    def open_salidas(self) -> None:
        if not self._guard_access("salidas", "Salidas"):
            return
        if not self._can_open_window():
            return
        w = SalidasWindow(self.root, usuario=self.user.get("nombre", ""), rol=self.user.get("rol", ""))
        self._track_window(w)

    def open_vigencias(self) -> None:
        if not self._guard_access("vigencias", "Vigencias"):
            return
        if not self._can_open_window():
            return
        w = VigenciasWindow(self.root, usuario=self.user.get("nombre", ""), rol=self.user.get("rol", ""))
        self._track_window(w)

    def open_stock(self) -> None:
        if not self._guard_access("stock", "Stock"):
            return
        if not self._can_open_window():
            return
        w = StockWindow(self.root)
        self._track_window(w)

    def open_stock_analista(self) -> None:
        if not self._guard_access("stock", "Stock Analista"):
            return
        if not self._can_open_window():
            return
        w = StockAnalistaWindow(self.root)
        self._track_window(w)

    def open_usuarios(self) -> None:
        if not self._guard_access("usuarios_admin", "Usuarios"):
            return
        if not self._can_open_window():
            return
        w = CreateUserWindow(self.root)
        self._track_window(w)

    def open_bitacora(self) -> None:
        if not self._guard_access("auditoria", "Reportes"):
            return
        if not self._can_open_window():
            return
        w = BitacoraWindow(self.root)
        self._track_window(w)

    def open_reportes(self) -> None:
        if not self._guard_access("auditoria", "Reportes"):
            return
        if not self._can_open_window():
            return
        w = ReportesWindow(self.root)
        self._track_window(w)

    def open_sustancias(self) -> None:
        if not self._guard_access("inventario", "Sustancias"):
            return
        if not self._can_open_window():
            return
        w = SubstanceMasterWindow(self.root)
        self._track_window(w)

    def open_tipo_entrada(self) -> None:
        if not self._guard_access("inventario", "T. Entrada"):
            return
        if not self._can_open_window():
            return
        w = MasterCatalogWindow(self.root, "T. Entrada", TIPOS_ENTRADA_FILE, "maestrasTiposEntrada", "nombre")
        self._track_window(w)

    def open_tipo_salida(self) -> None:
        if not self._guard_access("inventario", "T. Salida"):
            return
        if not self._can_open_window():
            return
        w = MasterCatalogWindow(self.root, "T. Salida", TIPOS_SALIDA_FILE, "maestrasTiposSalida", "nombre")
        self._track_window(w)

    def open_proveedor(self) -> None:
        if not self._guard_access("inventario", "Proveedor"):
            return
        if not self._can_open_window():
            return
        w = MasterCatalogWindow(self.root, "Proveedor", PROVEEDORES_FILE, "maestrasProveedores", "nombre")
        self._track_window(w)

    def open_almacen(self) -> None:
        if not self._guard_access("inventario", "C. Almace"):
            return
        if not self._can_open_window():
            return
        w = MasterCatalogWindow(self.root, "C. Almace", ALMACENES_FILE, "maestrasAlmacenes", "nombre")
        self._track_window(w)

    def open_unidad(self) -> None:
        if not self._guard_access("inventario", "Unidad"):
            return
        if not self._can_open_window():
            return
        w = MasterCatalogWindow(self.root, "Unidad", UNIDADES_FILE, "maestrasUnidades", "nombre")
        self._track_window(w)

    def open_ubicacion(self) -> None:
        if not self._guard_access("inventario", "Ubicación"):
            return
        if not self._can_open_window():
            return
        w = LocationMasterWindow(self.root)
        self._track_window(w)

    def open_condicion_almac(self) -> None:
        if not self._guard_access("inventario", "Cond. Almac."):
            return
        if not self._can_open_window():
            return
        w = MasterCatalogWindow(self.root, "Cond. Almac.", CONDICIONES_FILE, "maestrasCondicionesAlmacenamiento", "nombre")
        self._track_window(w)

    def _no_access(self, module_label: str = "este módulo") -> None:
        import tkinter.messagebox as mb
        mb.showerror("Permisos insuficientes", f"No tienes permisos para acceder a {module_label}.", parent=self.root)

    def _logout(self) -> None:
        """Cierra la sesión y vuelve al login."""
        for child in self.root.winfo_children():
            child.destroy()
        self.root.geometry("600x400")
        from ui.login import LoginWindow
        LoginWindow(self.root)

    def not_implemented(self) -> None:
        top = tk.Toplevel(self.root)
        top.title("Modulo en construccion")
        top.geometry("320x120")
        top.configure(bg="white")
        tk.Label(
            top,
            text="Este modulo estara disponible pronto.",
            bg="white",
            fg=COLORS["text_dark"],
            font=("Segoe UI", 10),
        ).pack(expand=True, padx=16, pady=16)
