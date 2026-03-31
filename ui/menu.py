import importlib
import tkinter as tk

from config.config import (
    ALMACENES_FILE,
    CONDICIONES_FILE,
    PROVEEDORES_FILE,
    TIPOS_ENTRADA_FILE,
    TIPOS_SALIDA_FILE,
    UBICACIONES_FILE,
    UNIDADES_FILE,
)
from config.config import COLORS, IMAGES_PATH
from ui.bitacora import BitacoraWindow
from ui.entradas import EntryFormWindow
from ui.maestras import MasterCatalogWindow, SubstanceMasterWindow
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
        self._build_ui()

    def _build_ui(self) -> None:
        self.root.configure(bg=COLORS["secondary"])
        self._set_balanced_geometry()

        wrapper = tk.Frame(self.root, bg=COLORS["secondary"], padx=18, pady=14)
        wrapper.pack(expand=True, fill="both")

        shell = tk.Frame(wrapper, bg="white", bd=1, relief="solid", padx=14, pady=12)
        shell.pack(expand=True, fill="both")

        top_label = tk.Label(
            shell,
            text="MENU PRINCIPAL",
            bg="white",
            fg="#2E2E2E",
            font=("Segoe UI", 12),
        )
        top_label.pack(anchor="w", pady=(0, 4))

        top = tk.Frame(shell, bg="white")
        top.pack(fill="x", pady=(0, 12))

        brand = tk.Frame(top, bg="white")
        brand.pack(side="left", fill="x", expand=True)
        tk.Label(
            brand,
            text="CECIF",
            bg="white",
            fg="#232323",
            font=("Segoe UI", 50, "bold"),
        ).pack(anchor="w", pady=(2, 0))
        tk.Label(
            brand,
            text="CENTRO DE LA CIENCIA Y LA INVESTIGACION FARMACEUTICA",
            bg="white",
            fg=COLORS["button_hover"],
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w", pady=(0, 4))
        tk.Label(
            brand,
            text=f"Usuario: {self.user.get('nombre', 'N/A')} ({self.user.get('rol', 'N/A')})",
            bg="white",
            fg=COLORS["text_dark"],
            font=("Segoe UI", 10),
        ).pack(anchor="w")

        top_right = tk.Frame(top, bg="white")
        top_right.pack(side="right", fill="y")

        tk.Label(
            top_right,
            text="CONTROL DE INVENTARIO",
            bg="white",
            fg=COLORS["primary"],
            font=("Segoe UI", 32, "bold"),
        ).pack(anchor="e", pady=(0, 4))
        tk.Button(
            top_right,
            text="Login",
            command=self.root.destroy,
            bg=COLORS["primary"],
            fg=COLORS["text_light"],
            relief="flat",
            font=("Segoe UI", 11, "bold"),
            padx=20,
            pady=5,
        ).pack(anchor="e")

        body = tk.Frame(shell, bg="white")
        body.pack(expand=True, fill="both")

        media_col = tk.LabelFrame(
            body,
            text="",
            bg="white",
            fg=COLORS["text_dark"],
            font=("Segoe UI", 11, "bold"),
            bd=1,
        )
        media_col.grid(row=0, column=0, sticky="nsew", padx=(0, 12), pady=(4, 0))

        image_placeholder = tk.Frame(media_col, bg="#ECEFF4", bd=1, relief="solid")
        image_placeholder.pack(expand=True, fill="both", padx=12, pady=12)
        self._render_main_image(image_placeholder)

        moves_col = tk.LabelFrame(
            body,
            text="Movimientos y Reportes",
            bg="white",
            fg=COLORS["text_dark"],
            font=("Segoe UI", 11, "bold"),
            bd=1,
        )
        moves_col.grid(row=0, column=1, sticky="nsew", padx=10, pady=(4, 0))

        masters_col = tk.LabelFrame(
            body,
            text="Maestras",
            bg="white",
            fg=COLORS["text_dark"],
            font=("Segoe UI", 11, "bold"),
            bd=1,
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
                ("Bitacora", self.open_bitacora, "auditoria"),
            ],
        )
        self._create_panel_buttons(
            masters_col,
            [
                ("Sustancias", self.open_sustancias, "inventario"),
                ("T. Entrada", self.open_tipo_entrada, "inventario"),
                ("T. Salida", self.open_tipo_salida, "inventario"),
                ("Proveedor", self.open_proveedor, "inventario"),
                ("Unidad", self.open_unidad, "inventario"),
                ("Ubicacion", self.open_ubicacion, "inventario"),
                ("Cond. Almac.", self.open_condicion_almac, "inventario"),
                ("C. Almace", self.open_almacen, "inventario"),
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

    def _get_button_image_path(self, label: str) -> str | None:
        """Mapea nombre de botón a archivo de imagen."""
        mapping = {
            "Entradas": "imgEntrada.png",
            "Salidas": "imgSalida.png",
            "Vigencia": "imgVigencia.png",
            "Stock": "imgStock.png",
            "Usuarios": "imgUsuario.png",
            "Bitacora": "imgReporte.png",
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
            img.thumbnail((55, 55), image_mod.LANCZOS if hasattr(image_mod, "LANCZOS") else 1)
            return image_tk_mod.PhotoImage(img)
        except Exception:
            return None

    def _create_panel_buttons(self, parent: tk.Widget, buttons: list[tuple[str, object, str]]) -> None:
        grid = tk.Frame(parent, bg="white")
        grid.pack(expand=True, fill="both", padx=8, pady=8)

        perms = self.user.get("permisos", {})
        is_admin = str(self.user.get("rol", "")).lower() == "admin"

        for idx, (label, callback, perm_key) in enumerate(buttons):
            row = idx // 2
            col = idx % 2
            has_access = is_admin or perms.get(perm_key, False)

            button_shell = tk.Frame(grid, bg="white", bd=1, relief="solid", padx=6, pady=10)
            button_shell.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

            icon_frame = tk.Frame(button_shell, bg="white")
            icon_frame.pack(side="left", padx=(0, 8))

            img_filename = self._get_button_image_path(label)
            if img_filename:
                icon_tk = self._load_button_icon(img_filename)
                if icon_tk:
                    self.button_images[label] = icon_tk
                    tk.Label(icon_frame, image=icon_tk, bg="white").pack()
                else:
                    tk.Label(icon_frame, text="□", bg="white", fg="#CCC", font=("Segoe UI", 14)).pack()
            else:
                tk.Label(icon_frame, text="□", bg="white", fg="#CCC", font=("Segoe UI", 14)).pack()

            btn = tk.Button(
                button_shell,
                text=label,
                command=callback if has_access else self._no_access,
                bg="white" if has_access else "#E0E0E0",
                fg=COLORS["text_dark"] if has_access else "#999999",
                relief="flat",
                bd=0,
                activebackground="white",
                activeforeground=COLORS["text_dark"],
                font=("Segoe UI", 11),
                anchor="w",
                padx=3,
                state="normal" if has_access else "disabled",
            )
            btn.pack(side="left", fill="both", expand=True)

        max_rows = (len(buttons) + 1) // 2
        for row in range(max_rows):
            grid.rowconfigure(row, weight=1)
        for col in range(2):
            grid.columnconfigure(col, weight=1)

    def open_entradas(self) -> None:
        EntryFormWindow(self.root, usuario=self.user.get("nombre", ""), rol=self.user.get("rol", ""))

    def open_salidas(self) -> None:
        SalidasWindow(self.root, usuario=self.user.get("nombre", ""), rol=self.user.get("rol", ""))

    def open_vigencias(self) -> None:
        VigenciasWindow(self.root)

    def open_stock(self) -> None:
        StockWindow(self.root)

    def open_usuarios(self) -> None:
        CreateUserWindow(self.root)

    def open_bitacora(self) -> None:
        BitacoraWindow(self.root)

    def open_sustancias(self) -> None:
        SubstanceMasterWindow(self.root)

    def open_tipo_entrada(self) -> None:
        MasterCatalogWindow(self.root, "T. Entrada", TIPOS_ENTRADA_FILE, "tipos_entrada", "nombre")

    def open_tipo_salida(self) -> None:
        MasterCatalogWindow(self.root, "T. Salida", TIPOS_SALIDA_FILE, "tipos_salida", "nombre")

    def open_proveedor(self) -> None:
        MasterCatalogWindow(self.root, "Proveedor", PROVEEDORES_FILE, "proveedores", "nombre")

    def open_almacen(self) -> None:
        MasterCatalogWindow(self.root, "C. Almace", ALMACENES_FILE, "almacenes", "nombre")

    def open_unidad(self) -> None:
        MasterCatalogWindow(self.root, "Unidad", UNIDADES_FILE, "unidades", "nombre")

    def open_ubicacion(self) -> None:
        MasterCatalogWindow(self.root, "Ubicacion", UBICACIONES_FILE, "ubicaciones", "nombre")

    def open_condicion_almac(self) -> None:
        MasterCatalogWindow(self.root, "Cond. Almac.", CONDICIONES_FILE, "condiciones_almacenamiento", "nombre")

    def _no_access(self) -> None:
        import tkinter.messagebox as mb
        mb.showwarning("Acceso denegado", "No tiene permisos para acceder a este módulo.")

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
