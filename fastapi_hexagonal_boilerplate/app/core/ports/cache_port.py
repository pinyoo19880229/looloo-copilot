from abc import ABC, abstractmethod
from typing import Any, Optional

class CachePort(ABC):
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> None:
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        pass
