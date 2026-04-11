"""
Migración única: reemplaza campos de texto desnormalizados por IDs (claves foráneas)
en los archivos JSON transaccionales y en algunas maestras.
"""

import json
import os
import shutil
import unicodedata
from datetime import datetime

from config.config import ENTRADAS_FILE, INVENTARIO_FILE, SALIDAS_FILE
from utils.data_handler import sync_inventario

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _load(fname: str) -> dict:
    path = os.path.join(DATA_DIR, fname)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _save(fname: str, data: dict) -> None:
    path = os.path.join(DATA_DIR, fname)
    bak = path + f".bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(path, bak)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  OK  {fname}  (backup: {os.path.basename(bak)})")


def _normalize_key(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.strip().lower()


def _build_map(records: list, key_field: str = "nombre") -> dict:
    result = {}
    for r in records:
        raw_key = str(r.get(key_field, "")).strip()
        rid = r.get("id")
        if raw_key and rid is not None:
            result[_normalize_key(raw_key)] = rid
    return result


def _build_location_map(ubicaciones: list, ubicaciones_uso: list) -> dict:
    result = {}
    for tipo, records in (("almacen", ubicaciones), ("uso", ubicaciones_uso)):
        for record in records:
            name = str(record.get("nombre", "")).strip()
            record_id = record.get("id")
            if name and record_id is not None:
                result[_normalize_key(name)] = (tipo, record_id)
    return result


def _set_location_fields(record: dict, legacy_field: str, location_map: dict) -> int:
    warnings = 0
    legacy_value = str(record.pop(legacy_field, "")).strip() if legacy_field in record else ""
    if record.get("id_ubicacion") is not None and record.get("ubicacion_tipo"):
        return warnings
    if not legacy_value:
        if legacy_field == "ubicacion":
            record.setdefault("ubicacion_tipo", "")
            record.setdefault("id_ubicacion", None)
        else:
            record.setdefault("ubicacion_origen_tipo", "")
            record.setdefault("id_ubicacion_origen", None)
        return warnings

    mapped = location_map.get(_normalize_key(legacy_value))
    if mapped is None:
        print(f"    AVISO: ubicación '{legacy_value}' no encontrada en maestras")
        warnings += 1
        mapped = ("", None)

    tipo, record_id = mapped
    if legacy_field == "ubicacion":
        record["ubicacion_tipo"] = tipo
        record["id_ubicacion"] = record_id
    else:
        record["ubicacion_origen_tipo"] = tipo
        record["id_ubicacion_origen"] = record_id
    return warnings


def migrate() -> None:
    print("Cargando tablas maestras...")

    te_map = _build_map(_load("maestrasTiposEntrada.json")["maestrasTiposEntrada"])
    ts_map = _build_map(_load("maestrasTiposSalida.json")["maestrasTiposSalida"])
    un_map = _build_map(_load("maestrasUnidades.json")["maestrasUnidades"])
    pv_map = _build_map(_load("maestrasProveedores.json")["maestrasProveedores"])
    ca_map = _build_map(
        _load("maestrasCondicionesAlmacenamiento.json")["maestrasCondicionesAlmacenamiento"]
    )
    al_map = _build_map(_load("maestrasAlmacenes.json")["maestrasAlmacenes"])
    sustancias = _load("maestrasSustancias.json").get("maestrasSustancias", [])
    sust_map = _build_map(sustancias, "codigo")
    ubicaciones = _load("maestrasUbicaciones.json").get("maestrasUbicaciones", [])
    ubicaciones_uso = _load("maestrasUbicacionesUso.json").get("maestrasUbicacionesUso", [])
    loc_map = _build_location_map(ubicaciones, ubicaciones_uso)

    print(f"  tipos_entrada:  {len(te_map)} entradas")
    print(f"  tipos_salida:   {len(ts_map)} entradas")
    print(f"  sustancias:     {len(sust_map)} entradas")
    print(f"  unidades:       {len(un_map)} entradas")
    print(f"  proveedores:    {len(pv_map)} entradas")
    print(f"  condiciones:    {len(ca_map)} entradas")
    print(f"  almacenes:      {len(al_map)} entradas")
    print(f"  ubicaciones:    {len(loc_map)} entradas")

    warnings = 0

    print("\nMigrando entradas.json ...")
    d = _load("entradas.json")
    for e in d.get("entradas", []):
        if "tipo_entrada" in e:
            val = str(e.pop("tipo_entrada", "")).strip()
            mapped = te_map.get(_normalize_key(val))
            if mapped is None and val:
                print(f"    AVISO: tipo_entrada '{val}' no encontrado en maestra (id={e.get('id')})")
                warnings += 1
            e["id_tipo_entrada"] = mapped

        if "codigo" in e and "id_sustancia" not in e:
            val = str(e.pop("codigo", "")).strip()
            mapped = sust_map.get(_normalize_key(val))
            if mapped is None and val:
                print(f"    AVISO: código de sustancia '{val}' no encontrado (id={e.get('id')})")
                warnings += 1
            e["id_sustancia"] = mapped
        e.pop("nombre", None)
        e.pop("codigo_contable", None)

        if "unidad" in e:
            val = str(e.pop("unidad", "")).strip()
            mapped = un_map.get(_normalize_key(val))
            if mapped is None and val:
                print(f"    AVISO: unidad '{val}' no encontrada en maestra (id={e.get('id')})")
                warnings += 1
            e["id_unidad"] = mapped

        if "proveedor" in e:
            val = str(e.pop("proveedor", "")).strip()
            mapped = pv_map.get(_normalize_key(val))
            if mapped is None and val:
                print(f"    AVISO: proveedor '{val}' no encontrado en maestra (id={e.get('id')})")
                warnings += 1
            e["id_proveedor"] = mapped

        if "condicion_almacenamiento" in e:
            val = str(e.pop("condicion_almacenamiento", "")).strip()
            mapped = ca_map.get(_normalize_key(val))
            if mapped is None and val:
                print(f"    AVISO: condición '{val[:40]}...' no encontrada en maestra (id={e.get('id')})")
                warnings += 1
            e["id_condicion_almacenamiento"] = mapped

        warnings += _set_location_fields(e, "ubicacion", loc_map)

    _save("entradas.json", d)

    print("Migrando salidas.json ...")
    d = _load("salidas.json")
    for s in d.get("salidas", []):
        if "tipo_salida" in s:
            val = str(s.pop("tipo_salida", "")).strip()
            mapped = ts_map.get(_normalize_key(val))
            if mapped is None and val:
                print(f"    AVISO: tipo_salida '{val}' no encontrado en maestra (id={s.get('id')})")
                warnings += 1
            s["id_tipo_salida"] = mapped

        if "codigo" in s and "id_sustancia" not in s:
            val = str(s.pop("codigo", "")).strip()
            mapped = sust_map.get(_normalize_key(val))
            if mapped is None and val:
                print(f"    AVISO: código de sustancia '{val}' no encontrado (id={s.get('id')})")
                warnings += 1
            s["id_sustancia"] = mapped
        s.pop("nombre", None)

        if "unidad" in s:
            val = str(s.pop("unidad", "")).strip()
            mapped = un_map.get(_normalize_key(val))
            if mapped is None and val:
                print(f"    AVISO: unidad '{val}' no encontrada en maestra (id={s.get('id')})")
                warnings += 1
            s["id_unidad"] = mapped

        warnings += _set_location_fields(s, "ubicacion_origen", loc_map)

    _save("salidas.json", d)

    print("Migrando maestrasSustancias.json ...")
    d = _load("maestrasSustancias.json")
    for s in d.get("maestrasSustancias", []):
        if "unidad" in s:
            val = str(s.pop("unidad", "")).strip()
            mapped = un_map.get(_normalize_key(val))
            if mapped is None and val:
                print(f"    AVISO: unidad '{val}' no encontrada en maestra (codigo={s.get('codigo')})")
                warnings += 1
            s["id_unidad"] = mapped

        warnings += _set_location_fields(s, "ubicacion", loc_map)
        s.pop("concentracion", None)
        s.pop("densidad", None)

    _save("maestrasSustancias.json", d)

    print("Migrando maestrasUbicaciones.json ...")
    d = _load("maestrasUbicaciones.json")
    for u in d.get("maestrasUbicaciones", []):
        if "almacen" in u:
            val = str(u.pop("almacen", "")).strip()
            mapped = al_map.get(_normalize_key(val)) if val else None
            if mapped is None and val:
                print(f"    AVISO: almacén '{val}' no encontrado (id={u.get('id')})")
                warnings += 1
            u["id_almacen"] = mapped

    _save("maestrasUbicaciones.json", d)

    sync_inventario(ENTRADAS_FILE, SALIDAS_FILE, INVENTARIO_FILE)
    print("Regenerando inventario.json ...")
    print("  OK  inventario.json")

    print()
    if warnings:
        print(f"  {warnings} aviso(s): algunos valores no pudieron mapearse a un ID")
        print("  Revise los avisos anteriores.")
    print("Migración completada.")
    print()
    print("Campos normalizados:")
    print("  entradas.json:            tipo_entrada, sustancia, unidad, proveedor, condición, ubicación")
    print("  salidas.json:             tipo_salida, sustancia, unidad, ubicación origen")
    print("  maestrasSustancias.json:  unidad y ubicación; sin concentración/densidad")
    print("  maestrasUbicaciones.json: almacén -> id_almacen")
    print("  inventario.json:          regenerado con ids")


if __name__ == "__main__":
    migrate()
