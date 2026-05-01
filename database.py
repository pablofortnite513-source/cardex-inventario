"""
database.py  -  Capa de acceso a datos - Kardex de Reactivos (CECIF)
=====================================================================
Soporta dos motores:
  - SQLite  (desarrollo local, sin servidor)
  - SQL Server (produccion, via pyodbc)

Uso:
    from database import get_db

    db = get_db()
    sustancias = db.get_sustancias()
    db.close()

Cambiar de SQLite a SQL Server: solo editar config.json
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Optional

try:
    import pyodbc
    _PYODBC_DISPONIBLE = True
except ImportError:
    _PYODBC_DISPONIBLE = False


# -- Resolucion de ruta base -------------------------------------------------

def _ruta_base() -> str:
    return os.path.dirname(os.path.abspath(__file__))


CONFIG_PATH = os.path.join(_ruta_base(), "config.json")

CONFIG_DEFAULT = {
    "motor": "sqlite",
    "sqlite": {"path": "data/kardex_reactivos.db"},
    "sqlserver": {
        "server": "NOMBRE_SERVIDOR",
        "database": "KardexReactivos",
        "driver": "ODBC Driver 17 for SQL Server",
        "trusted_connection": True,
        "username": "",
        "password": "",
    },
}


def _cargar_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(CONFIG_DEFAULT, f, indent=4, ensure_ascii=False)
    return CONFIG_DEFAULT


# -- Creacion de esquema -------------------------------------------------------

def _init_schema(conn):
    """Crea todas las tablas si no existen. Idempotente."""
    conn.executescript("""
        PRAGMA foreign_keys = OFF;

        -- Catalogos simples (todos: id + nombre + habilitada) ----------------

        CREATE TABLE IF NOT EXISTS proveedores (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre    TEXT NOT NULL,
            habilitada INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS unidades (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre    TEXT NOT NULL,
            habilitada INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS condiciones_almacenamiento (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre    TEXT NOT NULL,
            habilitada INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS almacenes (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre    TEXT NOT NULL,
            habilitada INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS tipos_entrada (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre    TEXT NOT NULL,
            habilitada INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS tipos_salida (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre    TEXT NOT NULL,
            habilitada INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS ubicaciones (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre    TEXT NOT NULL,
            habilitada INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS ubicaciones_uso (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre    TEXT NOT NULL,
            habilitada INTEGER NOT NULL DEFAULT 1
        );

        -- Sustancias ----------------------------------------------------------

        CREATE TABLE IF NOT EXISTS sustancias (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo                TEXT NOT NULL UNIQUE,
            nombre                TEXT NOT NULL,
            codigo_cas            TEXT,
            controlada            TEXT,
            limite_minimo_control TEXT,
            codigo_sistema        TEXT,
            cantidad_minima_stock REAL    NOT NULL DEFAULT 0,
            ubicacion_tipo        TEXT,
            id_ubicacion          INTEGER,
            id_unidad             INTEGER,
            habilitada            INTEGER NOT NULL DEFAULT 1
        );

        -- Usuarios ------------------------------------------------------------

        CREATE TABLE IF NOT EXISTS usuarios (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario        TEXT NOT NULL UNIQUE,
            contrasena     TEXT NOT NULL,
            nombre         TEXT,
            rol            TEXT,
            estado         TEXT NOT NULL DEFAULT 'HABILITADA',
            firma_path     TEXT,
            firma_password TEXT
        );

        CREATE TABLE IF NOT EXISTS permisos_usuario (
            id_usuario  INTEGER PRIMARY KEY REFERENCES usuarios(id),
            inventario  INTEGER NOT NULL DEFAULT 0,
            entradas    INTEGER NOT NULL DEFAULT 0,
            salidas     INTEGER NOT NULL DEFAULT 0,
            stock       INTEGER NOT NULL DEFAULT 0,
            consulta    INTEGER NOT NULL DEFAULT 0,
            vigencias   INTEGER NOT NULL DEFAULT 0,
            auditoria   INTEGER NOT NULL DEFAULT 0
        );

        -- Entradas (lotes de reactivos - entidad principal) -------------------

        CREATE TABLE IF NOT EXISTS entradas (
            id                          INTEGER PRIMARY KEY AUTOINCREMENT,
            id_tipo_entrada             INTEGER REFERENCES tipos_entrada(id),
            fecha                       TEXT,
            id_sustancia                INTEGER REFERENCES sustancias(id),
            lote                        TEXT,
            cantidad                    REAL,
            presentacion                TEXT,
            total                       REAL,
            id_unidad                   INTEGER REFERENCES unidades(id),
            id_proveedor                INTEGER REFERENCES proveedores(id),
            concentracion               TEXT,
            densidad                    TEXT,
            costo_unitario              TEXT,
            costo_total                 TEXT,
            factura                     TEXT,
            certificado                 INTEGER NOT NULL DEFAULT 0,
            msds                        INTEGER NOT NULL DEFAULT 0,
            fecha_vencimiento           TEXT,
            fecha_documento             TEXT,
            vigencia_documento          TEXT,
            id_condicion_almacenamiento INTEGER REFERENCES condiciones_almacenamiento(id),
            ubicacion_tipo              TEXT,
            id_ubicacion                INTEGER,
            observaciones               TEXT,
            anulado                     INTEGER NOT NULL DEFAULT 0,
            motivo_anulacion            TEXT
        );

        -- Salidas (consumos / movimientos de salida) --------------------------

        CREATE TABLE IF NOT EXISTS salidas (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_salida         TEXT,
            id_tipo_salida       INTEGER REFERENCES tipos_salida(id),
            id_sustancia         INTEGER REFERENCES sustancias(id),
            lote                 TEXT,
            cantidad             REAL,
            id_unidad            INTEGER REFERENCES unidades(id),
            densidad             TEXT,
            ubicacion_origen_tipo TEXT,
            id_ubicacion_origen  INTEGER,
            peso_inicial         TEXT,
            peso_final           TEXT,
            liquido              INTEGER NOT NULL DEFAULT 0,
            en_uso               INTEGER NOT NULL DEFAULT 1,
            observaciones        TEXT,
            anulado              INTEGER NOT NULL DEFAULT 0,
            motivo_anulacion     TEXT
        );

        -- Bitacora (incluye columna hoja - especifica de este proyecto) -------

        CREATE TABLE IF NOT EXISTS bitacora (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_hora     TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            usuario        TEXT,
            tipo_operacion TEXT,
            hoja           TEXT,
            id_registro    TEXT,
            campo          TEXT,
            valor_anterior TEXT,
            valor_nuevo    TEXT
        );

        -- Listas de chequeo de recepcion de compra ----------------------------

        CREATE TABLE IF NOT EXISTS checklists (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_recepcion      TEXT,
            id_proveedor         INTEGER REFERENCES proveedores(id),
            orden_compra         TEXT,
            id_sustancia         INTEGER REFERENCES sustancias(id),
            codigo_producto      TEXT,
            lote                 TEXT,
            cantidad             REAL,
            observacion_producto TEXT,
            observaciones        TEXT,
            aprobo               TEXT,
            reviso               TEXT,
            verifico             TEXT,
            usuario              TEXT,
            estado               TEXT NOT NULL DEFAULT 'ACTIVO'
        );

        CREATE TABLE IF NOT EXISTS checklist_items (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            id_checklist INTEGER REFERENCES checklists(id),
            item         TEXT,
            respuesta    TEXT
        );

        PRAGMA foreign_keys = ON;

        CREATE INDEX IF NOT EXISTS idx_entradas_sustancia ON entradas(id_sustancia);
        CREATE INDEX IF NOT EXISTS idx_salidas_sustancia  ON salidas(id_sustancia);
        CREATE INDEX IF NOT EXISTS idx_bitacora_fecha      ON bitacora(fecha_hora);
        CREATE UNIQUE INDEX IF NOT EXISTS ux_entradas_sustancia_lote_activo
            ON entradas(id_sustancia, lote)
            WHERE anulado = 0 AND lote IS NOT NULL AND trim(lote) <> '';
    """)
    conn.commit()


# -- Migracion de esquema (idempotente) ----------------------------------------

def _col_existe(conn, tabla: str, columna: str) -> bool:
    cur = conn.execute(f"PRAGMA table_info({tabla})")
    return any(row[1] == columna for row in cur.fetchall())


def _migrar_schema(conn):
    """Agrega columnas faltantes a tablas existentes de forma idempotente."""
    conn.execute("PRAGMA foreign_keys = OFF")

    extra = {
        "sustancias": [
            ("controlada",            "TEXT"),
            ("limite_minimo_control", "TEXT"),
            ("codigo_cas",            "TEXT"),
            ("ubicacion_tipo",        "TEXT"),
            ("id_ubicacion",          "INTEGER"),
            ("id_unidad",             "INTEGER"),
        ],
        "entradas": [
            ("factura",      "TEXT"),
            ("certificado",  "INTEGER NOT NULL DEFAULT 0"),
            ("msds",         "INTEGER NOT NULL DEFAULT 0"),
        ],
        "salidas": [
            ("anulado",          "INTEGER NOT NULL DEFAULT 0"),
            ("motivo_anulacion", "TEXT"),
        ],
        "bitacora": [
            ("hoja", "TEXT"),
        ],
        "checklists": [
            ("codigo_producto", "TEXT"),
        ],
    }

    for tabla, cols in extra.items():
        for col, tipo in cols:
            if not _col_existe(conn, tabla, col):
                try:
                    conn.execute(f"ALTER TABLE {tabla} ADD COLUMN {col} {tipo}")
                except Exception:
                    pass

    # Índice único de respaldo para evitar lotes activos duplicados por sustancia.
    try:
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS ux_entradas_sustancia_lote_activo
                ON entradas(id_sustancia, lote)
                WHERE anulado = 0 AND lote IS NOT NULL AND trim(lote) <> ''
            """
        )
    except Exception:
        pass

    conn.execute("PRAGMA foreign_keys = ON")
    conn.commit()


# ============================================================================
# FUNCION PRINCIPAL: get_db()
# ============================================================================

def get_db() -> "KardexDB":
    """Devuelve una instancia de KardexDB conectada segun config.json."""
    cfg = _cargar_config()
    motor = cfg.get("motor", "sqlite").lower()

    if motor == "sqlserver":
        if not _PYODBC_DISPONIBLE:
            raise RuntimeError("pyodbc no esta instalado. Instala con: pip install pyodbc")
        sc = cfg["sqlserver"]
        if sc.get("trusted_connection"):
            conn_str = (
                f"DRIVER={{{sc['driver']}}};"
                f"SERVER={sc['server']};"
                f"DATABASE={sc['database']};"
                "Trusted_Connection=yes;"
            )
        else:
            conn_str = (
                f"DRIVER={{{sc['driver']}}};"
                f"SERVER={sc['server']};"
                f"DATABASE={sc['database']};"
                f"UID={sc['username']};PWD={sc['password']};"
            )
        conn = pyodbc.connect(conn_str)
        return KardexDB(conn, motor="sqlserver")

    # SQLite (predeterminado)
    sqlite_cfg = cfg.get("sqlite", {})
    db_path = sqlite_cfg.get("path", "data/kardex_reactivos.db")
    if not os.path.isabs(db_path):
        db_path = os.path.join(_ruta_base(), db_path)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    _init_schema(conn)
    _migrar_schema(conn)
    return KardexDB(conn, motor="sqlite")


# ============================================================================
# CLASE PRINCIPAL
# ============================================================================

class KardexDB:
    """Interfaz unificada de acceso a datos. Funciona con SQLite y SQL Server."""

    def __init__(self, conn, motor: str = "sqlite"):
        self._conn = conn
        self._motor = motor
        self._cursor = conn.cursor()
        if motor == "sqlite":
            conn.execute("PRAGMA foreign_keys = ON")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def close(self):
        self._conn.close()

    def commit(self):
        self._conn.commit()

    @staticmethod
    def _validar_fecha(valor: str) -> str:
        """Devuelve valor si tiene formato YYYY-MM-DD, cadena vacia en caso contrario."""
        if not valor:
            return ""
        try:
            datetime.strptime(str(valor).strip(), "%Y-%m-%d")
            return str(valor).strip()
        except ValueError:
            return ""

    def _ph(self) -> str:
        return "?" if self._motor == "sqlite" else "%s"

    def _execute(self, sql: str, params: tuple = ()):
        self._cursor.execute(sql, params)
        return self._cursor

    def _fetchall(self, sql: str, params: tuple = ()) -> list:
        cur = self._execute(sql, params)
        if self._motor == "sqlite":
            cols = [c[0] for c in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
        return [dict(zip([c[0] for c in cur.description], row)) for row in cur.fetchall()]

    def _fetchone(self, sql: str, params: tuple = ()) -> Optional[dict]:
        cur = self._execute(sql, params)
        if self._motor == "sqlite":
            cols = [c[0] for c in cur.description]
            row = cur.fetchone()
            return dict(zip(cols, row)) if row else None
        row = cur.fetchone()
        return dict(zip([c[0] for c in cur.description], row)) if row else None

    def _insert(self, sql: str, params: tuple = ()) -> int:
        self._execute(sql, params)
        self._conn.commit()
        if self._motor == "sqlserver":
            row = self._fetchone("SELECT @@IDENTITY AS id")
            return int(row["id"]) if row else 0
        return self._cursor.lastrowid

    # =========================================================================
    # CATALOGOS SIMPLES (helper generico)
    # =========================================================================

    def _get_catalogo(self, tabla: str, orden: str = "nombre") -> list:
        return self._fetchall(f"SELECT * FROM {tabla} ORDER BY {orden}")

    def _crear_catalogo(self, tabla: str, nombre: str) -> int:
        ph = self._ph()
        return self._insert(
            f"INSERT INTO {tabla} (nombre, habilitada) VALUES ({ph},{ph})",
            (nombre, 1),
        )

    def _actualizar_catalogo(self, tabla: str, id_: int, nombre: str):
        ph = self._ph()
        self._execute(f"UPDATE {tabla} SET nombre={ph} WHERE id={ph}", (nombre, id_))
        self.commit()

    def _habilitar_catalogo(self, tabla: str, id_: int, habilitar: bool):
        ph = self._ph()
        self._execute(
            f"UPDATE {tabla} SET habilitada={ph} WHERE id={ph}",
            (1 if habilitar else 0, id_),
        )
        self.commit()

    # =========================================================================
    # PROVEEDORES
    # =========================================================================

    def get_proveedores(self) -> list:
        return self._get_catalogo("proveedores")

    def crear_proveedor(self, nombre: str) -> int:
        return self._crear_catalogo("proveedores", nombre)

    def actualizar_proveedor(self, id_: int, nombre: str):
        self._actualizar_catalogo("proveedores", id_, nombre)

    def habilitar_proveedor(self, id_: int):
        self._habilitar_catalogo("proveedores", id_, True)

    def inhabilitar_proveedor(self, id_: int):
        self._habilitar_catalogo("proveedores", id_, False)

    # =========================================================================
    # UNIDADES
    # =========================================================================

    def get_unidades(self) -> list:
        return self._get_catalogo("unidades")

    def crear_unidad(self, nombre: str) -> int:
        return self._crear_catalogo("unidades", nombre)

    def actualizar_unidad(self, id_: int, nombre: str):
        self._actualizar_catalogo("unidades", id_, nombre)

    def habilitar_unidad(self, id_: int):
        self._habilitar_catalogo("unidades", id_, True)

    def inhabilitar_unidad(self, id_: int):
        self._habilitar_catalogo("unidades", id_, False)

    # =========================================================================
    # CONDICIONES DE ALMACENAMIENTO
    # =========================================================================

    def get_condiciones(self) -> list:
        return self._get_catalogo("condiciones_almacenamiento")

    def crear_condicion(self, nombre: str) -> int:
        return self._crear_catalogo("condiciones_almacenamiento", nombre)

    def actualizar_condicion(self, id_: int, nombre: str):
        self._actualizar_catalogo("condiciones_almacenamiento", id_, nombre)

    def habilitar_condicion(self, id_: int):
        self._habilitar_catalogo("condiciones_almacenamiento", id_, True)

    def inhabilitar_condicion(self, id_: int):
        self._habilitar_catalogo("condiciones_almacenamiento", id_, False)

    # =========================================================================
    # ALMACENES
    # =========================================================================

    def get_almacenes(self) -> list:
        return self._get_catalogo("almacenes")

    def crear_almacen(self, nombre: str) -> int:
        return self._crear_catalogo("almacenes", nombre)

    def actualizar_almacen(self, id_: int, nombre: str):
        self._actualizar_catalogo("almacenes", id_, nombre)

    def habilitar_almacen(self, id_: int):
        self._habilitar_catalogo("almacenes", id_, True)

    def inhabilitar_almacen(self, id_: int):
        self._habilitar_catalogo("almacenes", id_, False)

    # =========================================================================
    # TIPOS ENTRADA
    # =========================================================================

    def get_tipos_entrada(self, solo_habilitados: bool = False) -> list:
        if solo_habilitados:
            return self._fetchall("SELECT * FROM tipos_entrada WHERE habilitada=1 ORDER BY nombre")
        return self._get_catalogo("tipos_entrada")

    def crear_tipo_entrada(self, nombre: str) -> int:
        return self._crear_catalogo("tipos_entrada", nombre)

    def actualizar_tipo_entrada(self, id_: int, nombre: str, habilitada: bool = True):
        ph = self._ph()
        self._execute(
            f"UPDATE tipos_entrada SET nombre={ph}, habilitada={ph} WHERE id={ph}",
            (nombre, 1 if habilitada else 0, id_),
        )
        self.commit()

    def habilitar_tipo_entrada(self, id_: int):
        self._habilitar_catalogo("tipos_entrada", id_, True)

    def inhabilitar_tipo_entrada(self, id_: int):
        self._habilitar_catalogo("tipos_entrada", id_, False)

    # =========================================================================
    # TIPOS SALIDA
    # =========================================================================

    def get_tipos_salida(self, solo_habilitados: bool = False) -> list:
        if solo_habilitados:
            return self._fetchall("SELECT * FROM tipos_salida WHERE habilitada=1 ORDER BY nombre")
        return self._get_catalogo("tipos_salida")

    def crear_tipo_salida(self, nombre: str) -> int:
        return self._crear_catalogo("tipos_salida", nombre)

    def actualizar_tipo_salida(self, id_: int, nombre: str, habilitada: bool = True):
        ph = self._ph()
        self._execute(
            f"UPDATE tipos_salida SET nombre={ph}, habilitada={ph} WHERE id={ph}",
            (nombre, 1 if habilitada else 0, id_),
        )
        self.commit()

    def habilitar_tipo_salida(self, id_: int):
        self._habilitar_catalogo("tipos_salida", id_, True)

    def inhabilitar_tipo_salida(self, id_: int):
        self._habilitar_catalogo("tipos_salida", id_, False)

    # =========================================================================
    # UBICACIONES (almacen)
    # =========================================================================

    def get_ubicaciones(self) -> list:
        return self._get_catalogo("ubicaciones")

    def crear_ubicacion(self, nombre: str) -> int:
        return self._crear_catalogo("ubicaciones", nombre)

    def actualizar_ubicacion(self, id_: int, nombre: str):
        self._actualizar_catalogo("ubicaciones", id_, nombre)

    def habilitar_ubicacion(self, id_: int):
        self._habilitar_catalogo("ubicaciones", id_, True)

    def inhabilitar_ubicacion(self, id_: int):
        self._habilitar_catalogo("ubicaciones", id_, False)

    # =========================================================================
    # UBICACIONES USO
    # =========================================================================

    def get_ubicaciones_uso(self) -> list:
        return self._get_catalogo("ubicaciones_uso")

    def crear_ubicacion_uso(self, nombre: str) -> int:
        return self._crear_catalogo("ubicaciones_uso", nombre)

    def actualizar_ubicacion_uso(self, id_: int, nombre: str):
        self._actualizar_catalogo("ubicaciones_uso", id_, nombre)

    def habilitar_ubicacion_uso(self, id_: int):
        self._habilitar_catalogo("ubicaciones_uso", id_, True)

    def inhabilitar_ubicacion_uso(self, id_: int):
        self._habilitar_catalogo("ubicaciones_uso", id_, False)

    # =========================================================================
    # SUSTANCIAS
    # =========================================================================

    def get_sustancias(self) -> list:
        rows = self._fetchall("SELECT * FROM sustancias ORDER BY codigo")
        # Compatibilidad con campos legacy del JSON
        for r in rows:
            r.setdefault("sustancia_controlada", r.get("controlada", ""))
            r.setdefault("cantidad_minima", r.get("cantidad_minima_stock", 0))
            r["habilitada"] = bool(r.get("habilitada", 1))
        return rows

    def crear_sustancia(self, datos: dict) -> int:
        ph = self._ph()
        return self._insert(
            f"""INSERT INTO sustancias
                (codigo, nombre, codigo_cas, controlada, limite_minimo_control,
                 codigo_sistema, cantidad_minima_stock, ubicacion_tipo, id_ubicacion,
                 id_unidad, habilitada)
                VALUES ({ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph})""",
            (
                datos.get("codigo", ""),
                datos.get("nombre", ""),
                datos.get("codigo_cas", datos.get("propiedad", "")),
                datos.get("controlada", datos.get("sustancia_controlada", "")),
                datos.get("limite_minimo_control", ""),
                datos.get("codigo_sistema", ""),
                _safe_float(datos.get("cantidad_minima_stock", datos.get("cantidad_minima", 0))),
                datos.get("ubicacion_tipo", ""),
                datos.get("id_ubicacion"),
                datos.get("id_unidad"),
                1 if datos.get("habilitada", True) else 0,
            ),
        )

    def actualizar_sustancia(self, id_: int, datos: dict):
        ph = self._ph()
        fields = {
            "codigo":                datos.get("codigo"),
            "nombre":                datos.get("nombre"),
            "codigo_cas":            datos.get("codigo_cas", datos.get("propiedad")),
            "controlada":            datos.get("controlada", datos.get("sustancia_controlada")),
            "limite_minimo_control": datos.get("limite_minimo_control"),
            "codigo_sistema":        datos.get("codigo_sistema"),
            "cantidad_minima_stock": _safe_float(datos.get("cantidad_minima_stock", datos.get("cantidad_minima"))),
            "ubicacion_tipo":        datos.get("ubicacion_tipo"),
            "id_ubicacion":          datos.get("id_ubicacion"),
            "id_unidad":             datos.get("id_unidad"),
        }
        if "habilitada" in datos:
            fields["habilitada"] = 1 if datos["habilitada"] else 0
        sets = ", ".join([f"{k}={ph}" for k in fields])
        vals = list(fields.values()) + [id_]
        self._execute(f"UPDATE sustancias SET {sets} WHERE id={ph}", tuple(vals))
        self.commit()

    def habilitar_sustancia(self, id_: int):
        self._habilitar_catalogo("sustancias", id_, True)

    def inhabilitar_sustancia(self, id_: int):
        self._habilitar_catalogo("sustancias", id_, False)

    def save_sustancias(self, lista: list):
        """Guarda la lista completa de sustancias (usado en update desde JSON)."""
        for item in lista:
            id_ = item.get("id")
            if id_:
                self.actualizar_sustancia(id_, item)

    # =========================================================================
    # ENTRADAS (lotes de reactivos)
    # =========================================================================

    def get_entradas(self) -> list:
        rows = self._fetchall("SELECT * FROM entradas ORDER BY id")
        for r in rows:
            r["certificado"] = bool(r.get("certificado", 0))
            r["msds"] = bool(r.get("msds", 0))
            r["anulado"] = bool(r.get("anulado", 0))
        return rows

    def get_entradas_paginadas(self, pagina: int = 1, por_pagina: int = 50, filtros: dict | None = None) -> dict:
        """Retorna entradas paginadas con filtros opcionales."""
        pagina = max(1, int(pagina or 1))
        por_pagina = max(1, int(por_pagina or 50))
        offset = (pagina - 1) * por_pagina
        ph = self._ph()

        where_clauses: list[str] = []
        params: list = []

        if filtros:
            if filtros.get("fecha"):
                where_clauses.append(f"fecha = {ph}")
                params.append(filtros["fecha"])
            if filtros.get("id_sustancia") is not None:
                where_clauses.append(f"id_sustancia = {ph}")
                params.append(filtros["id_sustancia"])
            if filtros.get("lote"):
                where_clauses.append(f"lote LIKE {ph}")
                params.append(f"%{filtros['lote']}%")

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        count_sql = f"SELECT COUNT(*) as total FROM entradas {where_sql}"
        total_row = self._fetchone(count_sql, tuple(params)) or {"total": 0}
        total = int(total_row.get("total", 0) or 0)

        if self._motor == "sqlserver":
            data_sql = (
                f"SELECT * FROM entradas {where_sql} "
                f"ORDER BY fecha DESC, id DESC "
                f"OFFSET {ph} ROWS FETCH NEXT {ph} ROWS ONLY"
            )
        else:
            data_sql = (
                f"SELECT * FROM entradas {where_sql} "
                f"ORDER BY fecha DESC, id DESC "
                f"LIMIT {ph} OFFSET {ph}"
            )

        page_params = params + [offset, por_pagina] if self._motor == "sqlserver" else params + [por_pagina, offset]
        datos = self._fetchall(data_sql, tuple(page_params))
        for r in datos:
            r["certificado"] = bool(r.get("certificado", 0))
            r["msds"] = bool(r.get("msds", 0))
            r["anulado"] = bool(r.get("anulado", 0))

        return {
            "datos": datos,
            "total": total,
            "pagina": pagina,
            "total_paginas": max(1, (total + por_pagina - 1) // por_pagina),
            "por_pagina": por_pagina,
        }

    def crear_entrada(self, datos: dict) -> int:
        ph = self._ph()
        return self._insert(
            f"""INSERT INTO entradas
                (id_tipo_entrada, fecha, id_sustancia, lote, cantidad, presentacion, total,
                 id_unidad, id_proveedor, concentracion, densidad, costo_unitario, costo_total,
                 factura, certificado, msds, fecha_vencimiento, fecha_documento,
                 vigencia_documento, id_condicion_almacenamiento, ubicacion_tipo, id_ubicacion,
                 observaciones, anulado)
                VALUES ({ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},
                        {ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph})""",
            (
                datos.get("id_tipo_entrada"),
                datos.get("fecha", ""),
                datos.get("id_sustancia"),
                datos.get("lote", ""),
                _safe_float(datos.get("cantidad", 0)),
                datos.get("presentacion", ""),
                _safe_float(datos.get("total", 0)),
                datos.get("id_unidad"),
                datos.get("id_proveedor"),
                datos.get("concentracion", ""),
                datos.get("densidad", ""),
                datos.get("costo_unitario", ""),
                datos.get("costo_total", ""),
                datos.get("factura", ""),
                1 if datos.get("certificado") else 0,
                1 if datos.get("msds") else 0,
                datos.get("fecha_vencimiento", ""),
                datos.get("fecha_documento", ""),
                datos.get("vigencia_documento", ""),
                datos.get("id_condicion_almacenamiento"),
                datos.get("ubicacion_tipo", ""),
                datos.get("id_ubicacion"),
                datos.get("observaciones", ""),
                1 if datos.get("anulado") else 0,
            ),
        )

    def actualizar_entrada(self, id_: int, datos: dict):
        ph = self._ph()
        sets = []
        vals = []
        bool_fields = {"certificado", "msds", "anulado"}
        for campo, valor in datos.items():
            if campo == "id":
                continue
            sets.append(f"{campo}={ph}")
            if campo in bool_fields:
                vals.append(1 if valor else 0)
            else:
                vals.append(valor)
        if not sets:
            return
        vals.append(id_)
        self._execute(f"UPDATE entradas SET {', '.join(sets)} WHERE id={ph}", tuple(vals))
        self.commit()

    def anular_entrada(self, id_: int, motivo: str = ""):
        ph = self._ph()
        self._execute(
            f"UPDATE entradas SET anulado={ph}, motivo_anulacion={ph} WHERE id={ph}",
            (1, motivo, id_),
        )
        self.commit()

    # =========================================================================
    # SALIDAS (consumos)
    # =========================================================================

    def get_salidas(self) -> list:
        rows = self._fetchall("SELECT * FROM salidas ORDER BY id")
        for r in rows:
            r["liquido"] = bool(r.get("liquido", 0))
            r["en_uso"] = bool(r.get("en_uso", 1))
            r["anulado"] = bool(r.get("anulado", 0))
        return rows

    def crear_salida(self, datos: dict) -> int:
        ph = self._ph()
        return self._insert(
            f"""INSERT INTO salidas
                (fecha_salida, id_tipo_salida, id_sustancia, lote, cantidad, id_unidad,
                 densidad, ubicacion_origen_tipo, id_ubicacion_origen, peso_inicial,
                 peso_final, liquido, en_uso, observaciones, anulado)
                VALUES ({ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph})""",
            (
                datos.get("fecha_salida", ""),
                datos.get("id_tipo_salida"),
                datos.get("id_sustancia"),
                datos.get("lote", ""),
                _safe_float(datos.get("cantidad", 0)),
                datos.get("id_unidad"),
                datos.get("densidad", ""),
                datos.get("ubicacion_origen_tipo", ""),
                datos.get("id_ubicacion_origen"),
                datos.get("peso_inicial", ""),
                datos.get("peso_final", ""),
                1 if datos.get("liquido") else 0,
                1 if datos.get("en_uso", True) else 0,
                datos.get("observaciones", ""),
                1 if datos.get("anulado") else 0,
            ),
        )

    def actualizar_salida(self, id_: int, datos: dict):
        ph = self._ph()
        sets = []
        vals = []
        bool_fields = {"liquido", "en_uso", "anulado"}
        for campo, valor in datos.items():
            if campo == "id":
                continue
            sets.append(f"{campo}={ph}")
            vals.append(1 if valor else 0 if campo in bool_fields else valor)
        if not sets:
            return
        vals.append(id_)
        self._execute(f"UPDATE salidas SET {', '.join(sets)} WHERE id={ph}", tuple(vals))
        self.commit()

    def anular_salida(self, id_: int, motivo: str = ""):
        ph = self._ph()
        self._execute(
            f"UPDATE salidas SET anulado={ph}, motivo_anulacion={ph} WHERE id={ph}",
            (1, motivo, id_),
        )
        self.commit()

    # =========================================================================
    # BITACORA
    # =========================================================================

    def get_bitacora(self) -> list:
        return self._fetchall("SELECT * FROM bitacora ORDER BY id")

    def registrar_bitacora(
        self,
        usuario: str,
        tipo_operacion: str,
        hoja: str,
        id_registro: str,
        campo: str,
        valor_anterior: str,
        valor_nuevo: str,
    ) -> int:
        ph = self._ph()
        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self._insert(
            f"""INSERT INTO bitacora
                (fecha_hora, usuario, tipo_operacion, hoja, id_registro, campo,
                 valor_anterior, valor_nuevo)
                VALUES ({ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph})""",
            (fecha_hora, usuario, tipo_operacion, hoja, str(id_registro),
             campo, str(valor_anterior), str(valor_nuevo)),
        )

    # =========================================================================
    # USUARIOS
    # =========================================================================

    _PERM_CAMPOS = [
        "inventario", "entradas", "salidas", "stock", "consulta", "vigencias", "auditoria",
    ]

    def get_usuario_login(self, usuario: str, contrasena: str) -> Optional[dict]:
        u = self._fetchone(
            """SELECT u.id, u.usuario, u.contrasena, u.nombre, u.rol, u.estado,
                      u.firma_path, u.firma_password,
                      p.inventario, p.entradas, p.salidas, p.stock,
                      p.consulta, p.vigencias, p.auditoria
                 FROM usuarios u
                 LEFT JOIN permisos_usuario p ON p.id_usuario = u.id
                WHERE u.usuario = ? AND u.contrasena = ? AND u.estado = 'HABILITADA'""",
            (usuario, contrasena),
        )
        return self._normalizar_usuario(u) if u else None

    def get_usuarios(self) -> list:
        rows = self._fetchall(
            """SELECT u.id, u.usuario, u.contrasena, u.nombre, u.rol, u.estado,
                      u.firma_path, u.firma_password,
                      p.inventario, p.entradas, p.salidas, p.stock,
                      p.consulta, p.vigencias, p.auditoria
                 FROM usuarios u
                 LEFT JOIN permisos_usuario p ON p.id_usuario = u.id
                ORDER BY u.nombre"""
        )
        return [self._normalizar_usuario(u) for u in rows]

    def _normalizar_usuario(self, u: dict) -> dict:
        permisos = {c: bool(u.get(c, False)) for c in self._PERM_CAMPOS}
        return {
            "id":             u["id"],
            "usuario":        u["usuario"],
            "contrasena":     u.get("contrasena", ""),
            "nombre":         u.get("nombre", ""),
            "rol":            u.get("rol", ""),
            "estado":         u.get("estado", "HABILITADA"),
            "firma_path":     u.get("firma_path", ""),
            "firma_password": u.get("firma_password", ""),
            "permisos":       permisos,
        }

    def crear_usuario(self, datos: dict) -> int:
        ph = self._ph()
        uid = self._insert(
            f"""INSERT INTO usuarios
                (usuario, contrasena, nombre, rol, estado, firma_path, firma_password)
                VALUES ({ph},{ph},{ph},{ph},{ph},{ph},{ph})""",
            (
                datos["usuario"],
                datos["contrasena"],
                datos.get("nombre", ""),
                datos.get("rol", ""),
                datos.get("estado", "HABILITADA"),
                datos.get("firma_path", datos.get("permisos", {}).get("firma_path", "")),
                datos.get("firma_password", datos.get("permisos", {}).get("firma_password", "")),
            ),
        )
        self._insertar_permisos(uid, datos.get("permisos", {}))
        return uid

    def actualizar_usuario(self, id_usuario: int, datos: dict):
        ph = self._ph()
        self._execute(
            f"""UPDATE usuarios SET nombre={ph}, usuario={ph}, rol={ph}, estado={ph},
                firma_path={ph}, firma_password={ph} WHERE id={ph}""",
            (
                datos.get("nombre", ""),
                datos.get("usuario", ""),
                datos.get("rol", ""),
                datos.get("estado", "HABILITADA"),
                datos.get("firma_path", datos.get("permisos", {}).get("firma_path", "")),
                datos.get("firma_password", datos.get("permisos", {}).get("firma_password", "")),
                id_usuario,
            ),
        )
        if datos.get("contrasena"):
            self._execute(
                f"UPDATE usuarios SET contrasena={ph} WHERE id={ph}",
                (datos["contrasena"], id_usuario),
            )
        if "permisos" in datos:
            self._actualizar_permisos(id_usuario, datos["permisos"])
        self.commit()

    def eliminar_usuario(self, id_usuario: int):
        ph = self._ph()
        self._execute(f"DELETE FROM permisos_usuario WHERE id_usuario={ph}", (id_usuario,))
        self._execute(f"DELETE FROM usuarios WHERE id={ph}", (id_usuario,))
        self.commit()

    def habilitar_usuario(self, id_usuario: int):
        ph = self._ph()
        self._execute(f"UPDATE usuarios SET estado={ph} WHERE id={ph}", ("HABILITADA", id_usuario))
        self.commit()

    def inhabilitar_usuario(self, id_usuario: int):
        ph = self._ph()
        self._execute(f"UPDATE usuarios SET estado={ph} WHERE id={ph}", ("INHABILITADA", id_usuario))
        self.commit()

    def _insertar_permisos(self, id_usuario: int, permisos: dict):
        ph = self._ph()
        campos = self._PERM_CAMPOS
        vals = [int(bool(permisos.get(c, False))) for c in campos]
        cols = ",".join(campos)
        phs = ",".join([ph] * len(campos))
        self._execute(
            f"INSERT OR REPLACE INTO permisos_usuario (id_usuario,{cols}) VALUES ({ph},{phs})",
            (id_usuario, *vals),
        )
        self.commit()

    def _actualizar_permisos(self, id_usuario: int, permisos: dict):
        ph = self._ph()
        campos = self._PERM_CAMPOS
        sets = ", ".join([f"{c}={ph}" for c in campos])
        vals = [int(bool(permisos.get(c, False))) for c in campos]
        self._execute(
            f"UPDATE permisos_usuario SET {sets} WHERE id_usuario={ph}",
            (*vals, id_usuario),
        )
        # Si no existia la fila, insertar
        if self._cursor.rowcount == 0:
            self._insertar_permisos(id_usuario, permisos)
            return
        self.commit()

    # =========================================================================
    # CHECKLISTS
    # =========================================================================

    def get_checklists(self) -> list:
        checklists = self._fetchall("SELECT * FROM checklists ORDER BY id")
        for cl in checklists:
            items = self._fetchall(
                "SELECT item, respuesta FROM checklist_items WHERE id_checklist=? ORDER BY id",
                (cl["id"],),
            )
            cl["checklist"] = {it["item"]: it["respuesta"] for it in items}
        return checklists

    def crear_checklist(self, datos: dict) -> int:
        ph = self._ph()
        cl_id = self._insert(
            f"""INSERT INTO checklists
                (fecha_recepcion, id_proveedor, orden_compra, id_sustancia, codigo_producto,
                 lote, cantidad, observacion_producto, observaciones, aprobo, reviso,
                 verifico, usuario, estado)
                VALUES ({ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph})""",
            (
                datos.get("fecha_recepcion", ""),
                datos.get("id_proveedor"),
                datos.get("orden_compra", ""),
                datos.get("id_sustancia"),
                datos.get("codigo_producto", ""),
                datos.get("lote", ""),
                _safe_float(datos.get("cantidad", 0)),
                datos.get("observacion_producto", ""),
                datos.get("observaciones", ""),
                datos.get("aprobo", ""),
                datos.get("reviso", datos.get("aprobo", "")),
                datos.get("verifico", ""),
                datos.get("usuario", ""),
                "ACTIVO",
            ),
        )
        checklist_dict = datos.get("checklist", {})
        for item, respuesta in checklist_dict.items():
            self._execute(
                f"INSERT INTO checklist_items (id_checklist, item, respuesta) VALUES ({ph},{ph},{ph})",
                (cl_id, item, respuesta),
            )
        self.commit()
        return cl_id


# -- Utilidades ---------------------------------------------------------------

def _safe_float(value) -> float:
    if value is None:
        return 0.0
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return 0.0
