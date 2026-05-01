# CECIF - Kardex Reactivos

Sistema de gestión de inventario con interfaz Tkinter y persistencia en base de datos.

## Arquitectura actual

- Capa de datos en [database.py](database.py) con soporte híbrido:
	- SQLite para entorno local.
	- SQL Server para producción (vía pyodbc).
- Inicialización automática de esquema al iniciar la app con `init_db_hybrid()`.
- UI en carpeta [ui](ui).
- Adaptador de compatibilidad en [utils/data_handler.py](utils/data_handler.py).

## Configuración

El motor se define en [config.json](config.json):

- `"motor": "sqlite"` para local.
- `"motor": "sqlserver"` para servidor.

## Requisitos

- Python 3.10 o superior.
- Dependencias en [requirements.txt](requirements.txt):
	- Pillow
	- tkcalendar
	- openpyxl
	- pyodbc (solo necesario para SQL Server)

## Ejecución

1. Crear entorno virtual.
2. Instalar dependencias.
3. Ejecutar:

```bash
python main.py
```

## Nota operativa

Al iniciar, [main.py](main.py) llama a `init_db_hybrid()` para crear y migrar tablas e índices de forma idempotente según el motor configurado.
