import os
import json
from typing import Any, Dict
from .storage_interface import StorageInterface

ANALISYS_FILE = "analisys.json"

class AnalysisJsonStorage(StorageInterface):
    """
    Implementación de StorageInterface para gestionar los analisis
    """

    def load(self) -> Dict[str, Any]:
        if os.path.exists(ANALISYS_FILE):
            with open(ANALISYS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def save(self, data: Dict[str, Any]) -> None:
        os.makedirs(os.path.dirname(ANALISYS_FILE) or ".", exist_ok=True)
        with open(ANALISYS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)