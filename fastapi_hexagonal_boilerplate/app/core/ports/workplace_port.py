from abc import ABC, abstractmethod
from typing import List, Optional
from app.core.models.workplace import Workplace

class WorkplacePort(ABC):
    """
    Port for accessing workplace data.
    """

    @abstractmethod
    async def get_accessible_workplaces(self, user_id: Optional[str]) -> List[Workplace]:
        """
        Retrieves a list of workplaces accessible to the given user.
        If user_id is None (e.g., system access or public data), it might return all relevant workplaces.
        Actual authorization logic for 'user_id' will be part of the implementation.
        """
        pass

    @abstractmethod
    async def get_workplace_by_id(self, workplace_id: str) -> Optional[Workplace]:
        """
        Retrieves a specific workplace by its ID.
        """
        pass
