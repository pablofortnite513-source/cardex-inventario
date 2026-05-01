"""
data_handler.py  -  Adaptador de datos para Kardex de Reactivos (CECIF)
========================================================================
Todas las operaciones se redirigen a la base de datos SQLite/SQL Server
a traves de database.get_db().

Las constantes de ruta JSON (ENTRADAS_FILE, SALIDAS_FILE, etc.) se usan
como claves de enrutamiento: el adaptador las interpreta y delega a los
metodos correctos de KardexDB.
"""

from __future__ import annotations

import unicodedata
from typing import Any, Dict, List, Optional

from database import get_db


def _norm(value: Any) -> str:
    text = str(value or "").strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.lower()


def _file_key(file_path) -> str:
    return str(file_path).replace("\\", "/").split("/")[-1].replace(".json", "").lower()


# Claves de enrutamiento (nombre del archivo JSON sin extension, en minusculas)
_ROUTE_ENTRADAS        = "entradas"
_ROUTE_SALIDAS         = "salidas"
_ROUTE_BITACORA        = "bitacora"
_ROUTE_INVENTARIO      = "inventario"
_ROUTE_SUSTANCIAS      = "maestrassustancias"
_ROUTE_PROVEEDORES     = "maestrasproveedores"
_ROUTE_UNIDADES        = "maestrasunidades"
_ROUTE_UBICACIONES     = "maestrasubicaciones"
_ROUTE_UBICACIONES_USO = "maestrasubicacionesuso"
_ROUTE_TIPOS_ENTRADA   = "maestrastiposentrada"
_ROUTE_TIPOS_SALIDA    = "maestrastipossalida"
_ROUTE_CONDICIONES     = "maestrascondicionesalmacenamiento"
_ROUTE_ALMACENES       = "maestrasalmacenes"
_ROUTE_USERS           = "usuarios"
_ROUTE_CHECKLISTS      = "listaschequeorecepcioncompra"


def _route(file_path) -> str:
    return _file_key(file_path)


# ============================================================================
# Helpers de indices (usados por la UI)
# ============================================================================

class Lookups:
    def __init__(self, **catalogs: list) -> None:
        self._fwd: Dict[str, Dict[int, str]] = {}
        self._rev: Dict[str, Dict[str, int]] = {}
        for cat, records in catalogs.items():
            fwd: Dict[int, str] = {}
            rev: Dict[str, int] = {}
            for r in records:
                rid = r.get("id")
                name = str(r.get("nombre", "")).strip()
                if rid is not None:
                    fwd[rid] = name
                if name:
                    rev[name] = rid
            self._fwd[cat] = fwd
            self._rev[cat] = rev

    def to_name(self, catalog: str, record_id, default: str = "") -> str:
        if record_id is None:
            return default
        return self._fwd.get(catalog, {}).get(record_id, default)

    def to_id(self, catalog: str, name: str) -> Optional[int]:
        if not name:
            return None
        return self._rev.get(catalog, {}).get(name.strip())


def build_substance_indexes(records: List[Dict[str, Any]]) -> tuple:
    by_id: Dict[int, Dict[str, Any]] = {}
    by_code: Dict[str, Dict[str, Any]] = {}
    for record in records:
        record_id = record.get("id")
        code = str(record.get("codigo", "")).strip()
        if record_id is not None:
            by_id[record_id] = record
        if code:
            by_code[_norm(code)] = record
    return by_id, by_code


def substance_from_id(records_by_id, substance_id: Any):
    if substance_id is None:
        return None
    return records_by_id.get(substance_id)


def substance_from_code(records_by_code, code: str):
    if not code:
        return None
    return records_by_code.get(_norm(code))


def substance_code(record, records_by_id) -> str:
    substance = substance_from_id(records_by_id, record.get("id_sustancia"))
    if substance is not None:
        return str(substance.get("codigo", ""))
    return str(record.get("codigo", ""))


def substance_name(record, records_by_id) -> str:
    substance = substance_from_id(records_by_id, record.get("id_sustancia"))
    if substance is not None:
        return str(substance.get("nombre", ""))
    return str(record.get("nombre", ""))


def substance_code_system(record, records_by_id) -> str:
    substance = substance_from_id(records_by_id, record.get("id_sustancia"))
    if substance is not None:
        return str(substance.get("codigo_sistema", ""))
    return str(record.get("codigo_sistema", record.get("codigo_contable", "")))


def substance_cas(record, records_by_id) -> str:
    substance = substance_from_id(records_by_id, record.get("id_sustancia"))
    if substance is not None:
        return str(substance.get("codigo_cas", ""))
    return str(record.get("codigo_cas", record.get("cas", "")))


def build_location_indexes(ubicaciones, ubicaciones_uso) -> tuple:
    by_key: Dict[tuple, Dict[str, Any]] = {}
    by_name: Dict[str, tuple] = {}
    for tipo, records in (("almacen", ubicaciones), ("uso", ubicaciones_uso)):
        for record in records:
            record_id = record.get("id")
            name = str(record.get("nombre", "")).strip()
            if record_id is None:
                continue
            key = (tipo, record_id)
            by_key[key] = record
            if name:
                by_name[_norm(name)] = key
    return by_key, by_name


def location_tuple_from_name(by_name, name: str):
    if not name:
        return None
    return by_name.get(_norm(name))


def location_name(record, locations_by_key, tipo_field="ubicacion_tipo",
                  id_field="id_ubicacion", legacy_field="ubicacion") -> str:
    tipo = record.get(tipo_field)
    record_id = record.get(id_field)
    if tipo and record_id is not None:
        target = locations_by_key.get((str(tipo), record_id))
        if target is not None:
            return str(target.get("nombre", ""))
        for alt_tipo in ("almacen", "uso"):
            target = locations_by_key.get((alt_tipo, record_id))
            if target is not None:
                return str(target.get("nombre", ""))
    return str(record.get(legacy_field, ""))


def sync_inventario(entradas_file=None, salidas_file=None, inventario_file=None):
    """No-op: el stock se calcula directamente desde entradas y salidas."""
    pass


# ============================================================================
# DataHandler (adaptador principal)
# ============================================================================

class DataHandler:

    @staticmethod
    def load_json(file_path) -> dict:
        """Carga datos segun la ruta del archivo (redirige a la base de datos)."""
        route = _route(file_path)
        db = get_db()
        try:
            if route == _ROUTE_SUSTANCIAS:
                return {"maestrasSustancias": db.get_sustancias()}
            if route == _ROUTE_PROVEEDORES:
                return {"maestrasProveedores": db.get_proveedores()}
            if route == _ROUTE_UNIDADES:
                return {"maestrasUnidades": db.get_unidades()}
            if route == _ROUTE_UBICACIONES:
                return {"maestrasUbicaciones": db.get_ubicaciones()}
            if route == _ROUTE_UBICACIONES_USO:
                return {"maestrasUbicacionesUso": db.get_ubicaciones_uso()}
            if route == _ROUTE_TIPOS_ENTRADA:
                return {"maestrasTiposEntrada": db.get_tipos_entrada()}
            if route == _ROUTE_TIPOS_SALIDA:
                return {"maestrasTiposSalida": db.get_tipos_salida()}
            if route == _ROUTE_CONDICIONES:
                return {"maestrasCondicionesAlmacenamiento": db.get_condiciones()}
            if route == _ROUTE_ALMACENES:
                return {"maestrasAlmacenes": db.get_almacenes()}
            if route == _ROUTE_ENTRADAS:
                return {"entradas": db.get_entradas()}
            if route == _ROUTE_INVENTARIO:
                # Calcula stock por (id_sustancia) para compatibilidad con maestras.py
                entradas = db.get_entradas()
                salidas = db.get_salidas()
                stock_map: dict = {}
                for e in entradas:
                    if e.get("anulado"):
                        continue
                    sid = e.get("id_sustancia")
                    stock_map[sid] = stock_map.get(sid, 0.0) + float(e.get("total", 0) or 0)
                for s in salidas:
                    if s.get("anulado"):
                        continue
                    sid = s.get("id_sustancia")
                    if sid in stock_map:
                        stock_map[sid] -= float(s.get("cantidad", 0) or 0)
                inventario = [{"id_sustancia": sid, "stock": round(stock, 6)} for sid, stock in stock_map.items()]
                return {"inventario": inventario}
            if route == _ROUTE_SALIDAS:
                return {"salidas": db.get_salidas()}
            if route == _ROUTE_BITACORA:
                return {"bitacora": db.get_bitacora()}
            if route == _ROUTE_USERS:
                return {"usuarios": db.get_usuarios()}
            if route == _ROUTE_CHECKLISTS:
                return {"listasChequeoRecepcionCompra": db.get_checklists()}
        finally:
            db.close()
        return {}

    @staticmethod
    def get_all(file_path, key: str) -> list:
        data = DataHandler.load_json(file_path)
        return data.get(key, [])

    @staticmethod
    def save_json(file_path, data: dict) -> bool:
        """Guarda datos completos (usado para actualizaciones masivas de sustancias)."""
        route = _route(file_path)
        db = get_db()
        try:
            if route == _ROUTE_SUSTANCIAS:
                db.save_sustancias(data.get("maestrasSustancias", []))
                return True
            if route == _ROUTE_USERS:
                # Usado por delete_selected: sincroniza la lista completa, elimina los ausentes
                new_ids = {u["id"] for u in data.get("usuarios", []) if u.get("id") is not None}
                for current in db.get_usuarios():
                    if current.get("id") not in new_ids:
                        db.eliminar_usuario(current["id"])
                return True
        finally:
            db.close()
        return True

    @staticmethod
    def add_record(file_path, key: str, record: dict) -> bool:
        route = _route(file_path)
        db = get_db()
        try:
            if route in (_ROUTE_ENTRADAS, _ROUTE_INVENTARIO):
                new_id = db.crear_entrada(record)
                record["id"] = new_id
                return new_id is not None

            if route == _ROUTE_SALIDAS:
                new_id = db.crear_salida(record)
                record["id"] = new_id
                return new_id is not None

            if route == _ROUTE_BITACORA:
                db.registrar_bitacora(
                    usuario=record.get("usuario", ""),
                    tipo_operacion=record.get("tipo_operacion", ""),
                    hoja=record.get("hoja", ""),
                    id_registro=record.get("id_registro", ""),
                    campo=record.get("campo", ""),
                    valor_anterior=record.get("valor_anterior", ""),
                    valor_nuevo=record.get("valor_nuevo", ""),
                )
                return True

            if route == _ROUTE_SUSTANCIAS:
                new_id = db.crear_sustancia(record)
                record["id"] = new_id
                return new_id is not None

            if route == _ROUTE_PROVEEDORES:
                new_id = db.crear_proveedor(record.get("nombre", ""))
                record["id"] = new_id
                return new_id is not None

            if route == _ROUTE_UNIDADES:
                new_id = db.crear_unidad(record.get("nombre", ""))
                record["id"] = new_id
                return new_id is not None

            if route == _ROUTE_UBICACIONES:
                new_id = db.crear_ubicacion(record.get("nombre", ""))
                record["id"] = new_id
                return new_id is not None

            if route == _ROUTE_UBICACIONES_USO:
                new_id = db.crear_ubicacion_uso(record.get("nombre", ""))
                record["id"] = new_id
                return new_id is not None

            if route == _ROUTE_TIPOS_ENTRADA:
                new_id = db.crear_tipo_entrada(record.get("nombre", ""))
                record["id"] = new_id
                return new_id is not None

            if route == _ROUTE_TIPOS_SALIDA:
                new_id = db.crear_tipo_salida(record.get("nombre", ""))
                record["id"] = new_id
                return new_id is not None

            if route == _ROUTE_CONDICIONES:
                new_id = db.crear_condicion(record.get("nombre", ""))
                record["id"] = new_id
                return new_id is not None

            if route == _ROUTE_ALMACENES:
                new_id = db.crear_almacen(record.get("nombre", ""))
                record["id"] = new_id
                return new_id is not None

            if route == _ROUTE_USERS:
                new_id = db.crear_usuario(record)
                record["id"] = new_id
                return new_id is not None

            if route == _ROUTE_CHECKLISTS:
                new_id = db.crear_checklist(record)
                record["id"] = new_id
                return new_id is not None

        except Exception as exc:
            print(f"[DataHandler.add_record] Error en {route}: {exc}")
            return False
        finally:
            db.close()
        return False

    @staticmethod
    def update_record(file_path, key: str, record_id: int, updates: dict) -> bool:
        route = _route(file_path)
        db = get_db()
        try:
            if route in (_ROUTE_ENTRADAS, _ROUTE_INVENTARIO):
                if updates.get("anulado"):
                    db.anular_entrada(record_id, updates.get("motivo_anulacion", ""))
                else:
                    db.actualizar_entrada(record_id, updates)
                return True

            if route == _ROUTE_SALIDAS:
                if updates.get("anulado"):
                    db.anular_salida(record_id, updates.get("motivo_anulacion", ""))
                else:
                    db.actualizar_salida(record_id, updates)
                return True

            if route == _ROUTE_SUSTANCIAS:
                if "habilitada" in updates:
                    if updates["habilitada"] is False or updates["habilitada"] == 0:
                        db.inhabilitar_sustancia(record_id)
                    else:
                        db.habilitar_sustancia(record_id)
                else:
                    db.actualizar_sustancia(record_id, updates)
                return True

            if route == _ROUTE_PROVEEDORES:
                nombre = updates.get("nombre", "")
                if nombre:
                    db.actualizar_proveedor(record_id, nombre)
                estado = str(updates.get("estado", updates.get("habilitada", ""))).upper()
                if estado in ("INHABILITADA", "0", "FALSE"):
                    db.inhabilitar_proveedor(record_id)
                elif estado in ("HABILITADA", "1", "TRUE"):
                    db.habilitar_proveedor(record_id)
                return True

            if route == _ROUTE_UNIDADES:
                nombre = updates.get("nombre", "")
                if nombre:
                    db.actualizar_unidad(record_id, nombre)
                estado = str(updates.get("estado", updates.get("habilitada", ""))).upper()
                if estado in ("INHABILITADA", "0", "FALSE"):
                    db.inhabilitar_unidad(record_id)
                elif estado in ("HABILITADA", "1", "TRUE"):
                    db.habilitar_unidad(record_id)
                return True

            if route == _ROUTE_UBICACIONES:
                nombre = updates.get("nombre", "")
                if nombre:
                    db.actualizar_ubicacion(record_id, nombre)
                estado = str(updates.get("estado", updates.get("habilitada", ""))).upper()
                if estado in ("INHABILITADA", "0", "FALSE"):
                    db.inhabilitar_ubicacion(record_id)
                elif estado in ("HABILITADA", "1", "TRUE"):
                    db.habilitar_ubicacion(record_id)
                return True

            if route == _ROUTE_UBICACIONES_USO:
                nombre = updates.get("nombre", "")
                if nombre:
                    db.actualizar_ubicacion_uso(record_id, nombre)
                estado = str(updates.get("estado", updates.get("habilitada", ""))).upper()
                if estado in ("INHABILITADA", "0", "FALSE"):
                    db.inhabilitar_ubicacion_uso(record_id)
                elif estado in ("HABILITADA", "1", "TRUE"):
                    db.habilitar_ubicacion_uso(record_id)
                return True

            if route == _ROUTE_TIPOS_ENTRADA:
                nombre = updates.get("nombre", "")
                habilitada = updates.get("habilitada", updates.get("estado", "HABILITADA"))
                if nombre:
                    db.actualizar_tipo_entrada(record_id, nombre, habilitada not in (False, 0, "INHABILITADA", "DESHABILITADA"))
                elif str(habilitada).upper() in ("INHABILITADA", "DESHABILITADA", "0", "FALSE"):
                    db.inhabilitar_tipo_entrada(record_id)
                elif str(habilitada).upper() in ("HABILITADA", "1", "TRUE"):
                    db.habilitar_tipo_entrada(record_id)
                return True

            if route == _ROUTE_TIPOS_SALIDA:
                nombre = updates.get("nombre", "")
                habilitada = updates.get("habilitada", updates.get("estado", "HABILITADA"))
                if nombre:
                    db.actualizar_tipo_salida(record_id, nombre, habilitada not in (False, 0, "INHABILITADA", "DESHABILITADA"))
                elif str(habilitada).upper() in ("INHABILITADA", "DESHABILITADA", "0", "FALSE"):
                    db.inhabilitar_tipo_salida(record_id)
                elif str(habilitada).upper() in ("HABILITADA", "1", "TRUE"):
                    db.habilitar_tipo_salida(record_id)
                return True

            if route == _ROUTE_CONDICIONES:
                nombre = updates.get("nombre", "")
                if nombre:
                    db.actualizar_condicion(record_id, nombre)
                estado = str(updates.get("estado", updates.get("habilitada", ""))).upper()
                if estado in ("INHABILITADA", "0", "FALSE"):
                    db.inhabilitar_condicion(record_id)
                elif estado in ("HABILITADA", "1", "TRUE"):
                    db.habilitar_condicion(record_id)
                return True

            if route == _ROUTE_ALMACENES:
                nombre = updates.get("nombre", "")
                if nombre:
                    db.actualizar_almacen(record_id, nombre)
                estado = str(updates.get("estado", updates.get("habilitada", ""))).upper()
                if estado in ("INHABILITADA", "0", "FALSE"):
                    db.inhabilitar_almacen(record_id)
                elif estado in ("HABILITADA", "1", "TRUE"):
                    db.habilitar_almacen(record_id)
                return True

            if route == _ROUTE_USERS:
                db.actualizar_usuario(record_id, updates)
                return True

        except Exception as exc:
            print(f"[DataHandler.update_record] Error en {route}: {exc}")
            return False
        finally:
            db.close()
        return False

    @staticmethod
    def delete_record(file_path, key: str, record_id: int) -> bool:
        route = _route(file_path)
        db = get_db()
        try:
            if route == _ROUTE_USERS:
                db.eliminar_usuario(record_id)
                return True
        except Exception as exc:
            print(f"[DataHandler.delete_record] Error en {route}: {exc}")
            return False
        finally:
            db.close()
        return False
