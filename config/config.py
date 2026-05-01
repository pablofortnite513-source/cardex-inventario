# Configuración del Proyecto - CECIF Kardex Inventario
from pathlib import Path

# Colores (basados en imágenes del proyecto)
COLORS = {
    "primary": "#C94A7F",      # Rosa/Magenta
    "secondary": "#F0F0F0",     # Gris claro (fondo)
    "text_dark": "#333333",     # Texto oscuro
    "text_light": "#FFFFFF",    # Texto claro
    "button_hover": "#A83A6B",  # Rosa más oscura
    "border": "#DEDEDE",        # Bordes
    "success": "#4CAF50",       # Verde
    "error": "#F44336",         # Rojo
}

# Dimensiones de ventanas
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 600

# Proyecto
PROJECT_NAME = "CECIF - Kardex Reactivos"
VERSION = "1.0.0"

# Rutas
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data"
REPORTES_PATH = PROJECT_ROOT / "reportes"
IMAGES_PATH = PROJECT_ROOT / "Imagenes"
FIRMAS_PATH = PROJECT_ROOT / "firmas"

# Base de datos SQLite (única fuente de datos)
DB_PATH = DATA_PATH / "kardex_reactivos.db"

# Rutas JSON heredadas – se mantienen como constantes simbólicas para que
# el adaptador data_handler las use como claves de enrutamiento.  Ya NO
# apuntan a archivos reales; las operaciones se redirigen a la base de datos.
USERS_FILE = DATA_PATH / "usuarios.json"
SUSTANCIAS_FILE = DATA_PATH / "maestrasSustancias.json"
PROVEEDORES_FILE = DATA_PATH / "maestrasProveedores.json"
UNIDADES_FILE = DATA_PATH / "maestrasUnidades.json"
UBICACIONES_FILE = DATA_PATH / "maestrasUbicaciones.json"
UBICACIONES_USO_FILE = DATA_PATH / "maestrasUbicacionesUso.json"
INVENTARIO_FILE = DATA_PATH / "inventario.json"
ENTRADAS_FILE = DATA_PATH / "entradas.json"
TIPOS_ENTRADA_FILE = DATA_PATH / "maestrasTiposEntrada.json"
TIPOS_SALIDA_FILE = DATA_PATH / "maestrasTiposSalida.json"
CONDICIONES_FILE = DATA_PATH / "maestrasCondicionesAlmacenamiento.json"
ALMACENES_FILE = DATA_PATH / "maestrasAlmacenes.json"
SALIDAS_FILE = DATA_PATH / "salidas.json"
BITACORA_FILE = DATA_PATH / "bitacora.json"
CHECKLISTS_FILE = DATA_PATH / "listasChequeoRecepcionCompra.json"
