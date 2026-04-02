import importlib
import tkinter as tk

from config.config import (
    ALMACENES_FILE,
    CONDICIONES_FILE,
    IMAGES_PATH,
    PROVEEDORES_FILE,
    TIPOS_ENTRADA_FILE,
    TIPOS_SALIDA_FILE,
    UBICACIONES_FILE,
    UNIDADES_FILE,
)
from config.config import COLORS
from ui.bitacora import BitacoraWindow
from ui.entradas import EntryFormWindow
from ui.maestras import LocationMasterWindow, MasterCatalogWindow, SubstanceMasterWindow
from ui.salidas import SalidasWindow
from ui.stock import StockWindow
from ui.users import CreateUserWindow
from ui.vigencias import VigenciasWindow


class MainMenuWindow:
    """Menu principal del sistema."""

    def __init__(self, root: tk.Tk, user: dict):
        self.root = root
        self.user = user
        self.main_image_tk = None
        self.button_images = {}
        self._open_windows: list[tk.Toplevel] = []
        self._build_ui()

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
                ("Usuarios", self.open_usuarios, "inventario"),
                ("Reportes", self.open_bitacora, "auditoria"),
            ],
        )
        self._create_panel_buttons(
            masters_col,
            [
                ("Sustancias", self.open_sustancias, "inventario"),
                ("T. Entrada", self.open_tipo_entrada, "inventario"),
                ("T. Salida", self.open_tipo_salida, "inventario"),
                ("Proveedor", self.open_proveedor, "inventario"),
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

        perms = self.user.get("permisos", {})
        is_admin = str(self.user.get("rol", "")).lower() == "admin"

        for idx, (label, callback, perm_key) in enumerate(buttons):
            row = idx // 2
            col = idx % 2
            has_access = is_admin or perms.get(perm_key, False)

            cmd = callback if has_access else self._no_access
            fg = COLORS["text_dark"] if has_access else "#999999"
            bg = "white" if has_access else "#E0E0E0"
            state = "normal" if has_access else "disabled"

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
                state=state,
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

    def _can_open_window(self) -> bool:
        """Limita a 3 ventanas Toplevel abiertas simultáneamente."""
        self._open_windows = [w for w in self._open_windows if w.winfo_exists()]
        if len(self._open_windows) >= 3:
            import tkinter.messagebox as mb
            mb.showwarning("Límite", "Ya tienes 3 ventanas abiertas. Cierra alguna para abrir otra.")
            return False
        return True

    def _track_window(self, obj) -> None:
        """Registra la ventana Toplevel del objeto abierto."""
        win = getattr(obj, "window", None)
        if win is not None:
            self._open_windows.append(win)

    def open_entradas(self) -> None:
        if not self._can_open_window():
            return
        w = EntryFormWindow(self.root, usuario=self.user.get("nombre", ""), rol=self.user.get("rol", ""))
        self._track_window(w)

    def open_salidas(self) -> None:
        if not self._can_open_window():
            return
        w = SalidasWindow(self.root, usuario=self.user.get("nombre", ""), rol=self.user.get("rol", ""))
        self._track_window(w)

    def open_vigencias(self) -> None:
        if not self._can_open_window():
            return
        w = VigenciasWindow(self.root, usuario=self.user.get("nombre", ""), rol=self.user.get("rol", ""))
        self._track_window(w)

    def open_stock(self) -> None:
        if not self._can_open_window():
            return
        w = StockWindow(self.root)
        self._track_window(w)

    def open_usuarios(self) -> None:
        if not self._can_open_window():
            return
        w = CreateUserWindow(self.root)
        self._track_window(w)

    def open_bitacora(self) -> None:
        if not self._can_open_window():
            return
        w = BitacoraWindow(self.root)
        self._track_window(w)

    def open_sustancias(self) -> None:
        if not self._can_open_window():
            return
        w = SubstanceMasterWindow(self.root)
        self._track_window(w)

    def open_tipo_entrada(self) -> None:
        if not self._can_open_window():
            return
        w = MasterCatalogWindow(self.root, "T. Entrada", TIPOS_ENTRADA_FILE, "maestrasTiposEntrada", "nombre")
        self._track_window(w)

    def open_tipo_salida(self) -> None:
        if not self._can_open_window():
            return
        w = MasterCatalogWindow(self.root, "T. Salida", TIPOS_SALIDA_FILE, "maestrasTiposSalida", "nombre")
        self._track_window(w)

    def open_proveedor(self) -> None:
        if not self._can_open_window():
            return
        w = MasterCatalogWindow(self.root, "Proveedor", PROVEEDORES_FILE, "maestrasProveedores", "nombre")
        self._track_window(w)

    def open_almacen(self) -> None:
        if not self._can_open_window():
            return
        w = MasterCatalogWindow(self.root, "C. Almace", ALMACENES_FILE, "maestrasAlmacenes", "nombre")
        self._track_window(w)

    def open_unidad(self) -> None:
        if not self._can_open_window():
            return
        w = MasterCatalogWindow(self.root, "Unidad", UNIDADES_FILE, "maestrasUnidades", "nombre")
        self._track_window(w)

    def open_ubicacion(self) -> None:
        if not self._can_open_window():
            return
        w = LocationMasterWindow(self.root)
        self._track_window(w)

    def open_condicion_almac(self) -> None:
        if not self._can_open_window():
            return
        w = MasterCatalogWindow(self.root, "Cond. Almac.", CONDICIONES_FILE, "maestrasCondicionesAlmacenamiento", "nombre")
        self._track_window(w)

    def _no_access(self) -> None:
        import tkinter.messagebox as mb
        mb.showwarning("Acceso denegado", "No tiene permisos para acceder a este módulo.")

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
