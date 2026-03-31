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
IMAGES_PATH = PROJECT_ROOT / "Imagenes"
USERS_FILE = DATA_PATH / "usuarios.json"
SUSTANCIAS_FILE = DATA_PATH / "sustancias.json"
PROVEEDORES_FILE = DATA_PATH / "proveedores.json"
UNIDADES_FILE = DATA_PATH / "unidades.json"
UBICACIONES_FILE = DATA_PATH / "ubicaciones.json"
INVENTARIO_FILE = DATA_PATH / "inventario.json"
ENTRADAS_FILE = DATA_PATH / "entradas.json"
TIPOS_ENTRADA_FILE = DATA_PATH / "tipos_entrada.json"
TIPOS_SALIDA_FILE = DATA_PATH / "tipos_salida.json"
CONDICIONES_FILE = DATA_PATH / "condiciones_almacenamiento.json"
ALMACENES_FILE = DATA_PATH / "almacenes.json"
SALIDAS_FILE = DATA_PATH / "salidas.json"
BITACORA_FILE = DATA_PATH / "bitacora.json"
