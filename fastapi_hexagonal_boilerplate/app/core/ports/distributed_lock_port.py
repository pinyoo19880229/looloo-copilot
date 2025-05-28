from abc import ABC, abstractmethod
from typing import Optional

class DistributedLockPort(ABC):
    @abstractmethod
    async def acquire(self, lock_key: str, timeout: int = 10, expire: Optional[int] = None) -> bool: # Timeout for acquiring, expire for lock itself
        pass

    @abstractmethod
    async def release(self, lock_key: str) -> bool:
        pass

    @abstractmethod
    async def is_locked(self, lock_key: str) -> bool:
        pass
