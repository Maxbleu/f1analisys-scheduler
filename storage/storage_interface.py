from abc import ABC, abstractmethod
from typing import Any, Dict

class StorageInterface(ABC):
    """
    Interfaz para un gestor de almacenamiento.
    """

    @abstractmethod
    def load(self) -> Dict[str, Any]:
        """
        Carga los datos de almacenamiento y los devuelve como dict.
        """
        ...

    @abstractmethod
    def save(self, data: Dict[str, Any]) -> None:
        """
        Guarda el dict de datos en el soporte de almacenamiento.
        """
        ...