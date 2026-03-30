# CECIF - Kardex Reactivos
## Sistema de Gestión de Inventario

### Estructura del Proyecto

```
cardex-inventario/
├── main.py                      # Punto de entrada
├── ui/
│   ├── __init__.py
│   ├── login.py                 # Pantalla de login
│   ├── menu.py                  # Menú principal
│   └── forms.py                 # Formularios
├── data/                        # Datos en archivos planos (JSON)
│   ├── usuarios.json
│   ├── sustancias.json
│   ├── proveedores.json
│   ├── unidades.json
│   ├── ubicaciones.json
│   └── inventario.json
├── utils/
│   ├── __init__.py
│   └── data_handler.py          # Funciones para leer/escribir JSON
├── config/
│   └── config.py                # Configuración global
└── README.md
```

### Requisitos
- Python 3.7+
- Tkinter (incluido en Python)

### Ejecución
```bash
python main.py
```

### Credenciales por defecto
- **Usuario:** admin
- **Contraseña:** admin123

### Próximos pasos
1. Crear interfaz de Login
2. Crear Menú Principal
3. Crear Formularios (Entradas, Salidas, Stock)
4. Conectar lógica de datos
