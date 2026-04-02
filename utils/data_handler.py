import json
import os
from typing import Any, Dict, List, Optional


def sync_inventario(entradas_file, salidas_file, inventario_file):
    """Recalcula el inventario disponible a partir de entradas y salidas no anuladas."""
    entradas = DataHandler.get_all(entradas_file, "entradas")
    salidas = DataHandler.get_all(salidas_file, "salidas")

    stock: Dict[str, Dict[str, Any]] = {}

    for e in entradas:
        if e.get("anulado"):
            continue
        key = (e.get("codigo", ""), e.get("lote", ""))
        total = 0
        try:
            total = float(e.get("total", 0))
        except (ValueError, TypeError):
            total = 0
        if key not in stock:
            stock[key] = {
                "codigo": e.get("codigo", ""),
                "nombre": e.get("nombre", ""),
                "lote": e.get("lote", ""),
                "unidad": e.get("unidad", ""),
                "ubicacion": e.get("ubicacion", ""),
                "proveedor": e.get("proveedor", ""),
                "fecha_vencimiento": e.get("fecha_vencimiento", ""),
                "condicion_almacenamiento": e.get("condicion_almacenamiento", ""),
                "presentacion": e.get("presentacion", ""),
                "stock": 0,
            }
        stock[key]["stock"] += total

    for s in salidas:
        if s.get("anulado"):
            continue
        key = (s.get("codigo", ""), s.get("lote", ""))
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
