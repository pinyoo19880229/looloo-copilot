from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional

class DatabasePort(ABC):
    @abstractmethod
    async def connect(self) -> None:
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        pass

    @abstractmethod
    async def insert(self, collection: str, data: Dict[str, Any]) -> Any: # Returns ID of inserted document or similar
        pass

    @abstractmethod
    async def find_one(self, collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def find_many(self, collection: str, query: Dict[str, Any], limit: int = 0) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def update_one(self, collection: str, query: Dict[str, Any], data: Dict[str, Any]) -> bool: # Returns True if updated, False otherwise
        pass

    @abstractmethod
    async def update_many(self, collection: str, query: Dict[str, Any], data: Dict[str, Any]) -> int: # Returns number of updated documents
        pass

    @abstractmethod
    async def delete_one(self, collection: str, query: Dict[str, Any]) -> bool: # Returns True if deleted, False otherwise
        pass

    @abstractmethod
    async def delete_many(self, collection: str, query: Dict[str, Any]) -> int: # Returns number of deleted documents
        pass
