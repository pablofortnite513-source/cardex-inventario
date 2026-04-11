import json
import os
import unicodedata
from typing import Any, Dict, List, Optional


class Lookups:
    """Diccionarios de resolución ID ↔ nombre para catálogos maestros.

    Uso:
        lkp = Lookups(unidades=lista_unidades, proveedores=lista_proveedores)
        nombre = lkp.to_name("unidades", 1)   # → "Litro"
        id_    = lkp.to_id("unidades", "Litro")  # → 1
    """

    def __init__(self, **catalogs: list) -> None:
        self._fwd: Dict[str, Dict[int, str]] = {}   # catalog → {id: nombre}
        self._rev: Dict[str, Dict[str, int]] = {}   # catalog → {nombre: id}
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
        """Devuelve el nombre correspondiente al ID, o default si no se encuentra."""
        if record_id is None:
            return default
        return self._fwd.get(catalog, {}).get(record_id, default)

    def to_id(self, catalog: str, name: str) -> Optional[int]:
        """Devuelve el ID correspondiente al nombre, o None si no se encuentra."""
        if not name:
            return None
        return self._rev.get(catalog, {}).get(name.strip())


def _normalize_text(value: Any) -> str:
    text = str(value or "").strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.lower()


def build_substance_indexes(records: List[Dict[str, Any]]) -> tuple[Dict[int, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    by_id: Dict[int, Dict[str, Any]] = {}
    by_code: Dict[str, Dict[str, Any]] = {}
    for record in records:
        record_id = record.get("id")
        code = str(record.get("codigo", "")).strip()
        if record_id is not None:
            by_id[record_id] = record
        if code:
            by_code[_normalize_text(code)] = record
    return by_id, by_code


def substance_from_id(records_by_id: Dict[int, Dict[str, Any]], substance_id: Any) -> Dict[str, Any] | None:
    if substance_id is None:
        return None
    return records_by_id.get(substance_id)


def substance_from_code(records_by_code: Dict[str, Dict[str, Any]], code: str) -> Dict[str, Any] | None:
    norm = _normalize_text(code)
    if not norm:
        return None
    return records_by_code.get(norm)


def substance_code(record: Dict[str, Any], records_by_id: Dict[int, Dict[str, Any]]) -> str:
    substance = substance_from_id(records_by_id, record.get("id_sustancia"))
    if substance is not None:
        return str(substance.get("codigo", ""))
    return str(record.get("codigo", ""))


def substance_name(record: Dict[str, Any], records_by_id: Dict[int, Dict[str, Any]]) -> str:
    substance = substance_from_id(records_by_id, record.get("id_sustancia"))
    if substance is not None:
        return str(substance.get("nombre", ""))
    return str(record.get("nombre", ""))


def substance_code_system(record: Dict[str, Any], records_by_id: Dict[int, Dict[str, Any]]) -> str:
    substance = substance_from_id(records_by_id, record.get("id_sustancia"))
    if substance is not None:
        return str(substance.get("codigo_sistema", ""))
    return str(record.get("codigo_contable", ""))


def substance_cas(record: Dict[str, Any], records_by_id: Dict[int, Dict[str, Any]]) -> str:
    substance = substance_from_id(records_by_id, record.get("id_sustancia"))
    if substance is not None:
        return str(substance.get("codigo_cas", ""))
    return str(record.get("cas", ""))


def build_location_indexes(
    ubicaciones: List[Dict[str, Any]],
    ubicaciones_uso: List[Dict[str, Any]],
) -> tuple[Dict[tuple[str, int], Dict[str, Any]], Dict[str, tuple[str, int]]]:
    by_key: Dict[tuple[str, int], Dict[str, Any]] = {}
    by_name: Dict[str, tuple[str, int]] = {}

    for tipo, records in (("almacen", ubicaciones), ("uso", ubicaciones_uso)):
        for record in records:
            record_id = record.get("id")
            name = str(record.get("nombre", "")).strip()
            if record_id is None:
                continue
            key = (tipo, record_id)
            by_key[key] = record
            if name:
                by_name[_normalize_text(name)] = key

    return by_key, by_name


def location_tuple_from_name(by_name: Dict[str, tuple[str, int]], name: str) -> tuple[str, int] | None:
    norm = _normalize_text(name)
    if not norm:
        return None
    return by_name.get(norm)


def location_name(
    record: Dict[str, Any],
    locations_by_key: Dict[tuple[str, int], Dict[str, Any]],
    tipo_field: str = "ubicacion_tipo",
    id_field: str = "id_ubicacion",
    legacy_field: str = "ubicacion",
) -> str:
    tipo = record.get(tipo_field)
    record_id = record.get(id_field)
    if tipo and record_id is not None:
        target = locations_by_key.get((str(tipo), record_id))
        if target is not None:
            return str(target.get("nombre", ""))
    return str(record.get(legacy_field, ""))


def sync_inventario(entradas_file, salidas_file, inventario_file):
    """Recalcula el inventario disponible a partir de entradas y salidas no anuladas."""
    entradas = DataHandler.get_all(entradas_file, "entradas")
    salidas = DataHandler.get_all(salidas_file, "salidas")

    stock: Dict[str, Dict[str, Any]] = {}

    for e in entradas:
        if e.get("anulado"):
            continue
        key = (e.get("id_sustancia") or e.get("codigo", ""), e.get("lote", ""))
        total = 0
        try:
            total = float(e.get("total", 0))
        except (ValueError, TypeError):
            total = 0
        if key not in stock:
            stock[key] = {
                "id_sustancia": e.get("id_sustancia"),
                "lote": e.get("lote", ""),
                "id_unidad": e.get("id_unidad"),
                "ubicacion_tipo": e.get("ubicacion_tipo"),
                "id_ubicacion": e.get("id_ubicacion"),
                "id_proveedor": e.get("id_proveedor"),
                "fecha_vencimiento": e.get("fecha_vencimiento", ""),
                "id_condicion_almacenamiento": e.get("id_condicion_almacenamiento"),
                "presentacion": e.get("presentacion", ""),
                "stock": 0,
            }
        stock[key]["stock"] += total

    for s in salidas:
        if s.get("anulado"):
            continue
        key = (s.get("id_sustancia") or s.get("codigo", ""), s.get("lote", ""))
        cant = 0
        try:
            cant = float(s.get("cantidad", 0))
        except (ValueError, TypeError):
            cant = 0
        if key in stock:
            stock[key]["stock"] -= cant

    inventario = []
    idx = 1
    for info in stock.values():
        rec = dict(info)
        rec["id"] = idx
        rec["stock"] = round(rec["stock"], 4)
        inventario.append(rec)
        idx += 1

    DataHandler.save_json(inventario_file, {"inventario": inventario})


def remove_lote_from_inventario(inventario_file, codigo: str, lote: str) -> bool:
    """Elimina un lote específico del inventario."""
    data = DataHandler.load_json(inventario_file)
    records = data.get("inventario", [])
    filtered = [r for r in records if not (r.get("codigo") == codigo and r.get("lote") == lote)]
    if len(filtered) == len(records):
        return False
    data["inventario"] = filtered
    return DataHandler.save_json(inventario_file, data)

class DataHandler:
    """Manejo de archivos JSON para maestras e inventario"""
    
    @staticmethod
    def load_json(file_path: str) -> Dict[str, Any]:
        """Carga JSON desde archivo"""
        if not os.path.exists(file_path):
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error cargando {file_path}: {e}")
            return {}
    
    @staticmethod
    def save_json(file_path: str, data: Dict[str, Any]) -> bool:
        """Guarda JSON a archivo"""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error guardando {file_path}: {e}")
            return False
    
    @staticmethod
    def add_record(file_path: str, key: str, record: Dict[str, Any]) -> bool:
        """Agrega un registro a una lista en JSON"""
        data = DataHandler.load_json(file_path)
        if key not in data:
            data[key] = []
        
        # Auto-ID
        if data[key]:
            record['id'] = max([r.get('id', 0) for r in data[key]]) + 1
        else:
            record['id'] = 1
        
        data[key].append(record)
        return DataHandler.save_json(file_path, data)
    
    @staticmethod
    def get_all(file_path: str, key: str) -> List[Dict[str, Any]]:
        """Obtiene todos los registros de una clave"""
        data = DataHandler.load_json(file_path)
        return data.get(key, [])

    @staticmethod
    def update_record(file_path: str, key: str, record_id: int, updates: Dict[str, Any]) -> bool:
        """Actualiza un registro existente por su ID."""
        data = DataHandler.load_json(file_path)
        records = data.get(key, [])
        for rec in records:
            if rec.get("id") == record_id:
                rec.update(updates)
                return DataHandler.save_json(file_path, data)
        return False
