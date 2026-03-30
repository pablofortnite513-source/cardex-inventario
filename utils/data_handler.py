import json
import os
from typing import Any, Dict, List, Optional

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
