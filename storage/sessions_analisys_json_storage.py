import os
import json
from typing import Any, Dict
from .storage_interface import StorageInterface

SESSIONS_ANALISYS_FILE = "sessions_analisys.json"

class SessionsAnalisysJsonStorage(StorageInterface):
    """
    Implementación de StorageInterface para gestionar los analisis de las sesiones
    """

    def load(self) -> Dict[str, Any]:
        if os.path.exists(SESSIONS_ANALISYS_FILE):
            with open(SESSIONS_ANALISYS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def save(self, data: Dict[str, Any]) -> None:
        os.makedirs(os.path.dirname(SESSIONS_ANALISYS_FILE) or ".", exist_ok=True)
        with open(SESSIONS_ANALISYS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)