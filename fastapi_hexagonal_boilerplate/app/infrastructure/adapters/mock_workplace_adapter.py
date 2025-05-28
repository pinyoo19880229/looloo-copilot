from typing import List, Optional
from app.core.models.workplace import Workplace
from app.core.ports.workplace_port import WorkplacePort

# Mock database
MOCK_WORKPLACES_DB = {
    "wp1": Workplace(id="wp1", name="Main Library"),
    "wp2": Workplace(id="wp2", name="Downtown Branch"),
    "wp3": Workplace(id="wp3", name="Westside Annex"),
    "wp4": Workplace(id="wp4", name="Special Collections (Restricted)"),
}

# Mock user access (simplified)
USER_ACCESS_DB = {
    "user123": ["wp1", "wp2", "wp3"],
    "user456": ["wp2", "wp3"],
    "admin789": ["wp1", "wp2", "wp3", "wp4"], # Admin has access to all
}

class MockWorkplaceAdapter(WorkplacePort):
    """
    Mock implementation of the WorkplacePort.
    Simulates fetching workplace data from a predefined dictionary.
    """

    async def get_accessible_workplaces(self, user_id: Optional[str]) -> List[Workplace]:
        if user_id and user_id in USER_ACCESS_DB:
            accessible_ids = USER_ACCESS_DB[user_id]
            return [MOCK_WORKPLACES_DB[wp_id] for wp_id in accessible_ids if wp_id in MOCK_WORKPLACES_DB]
        elif not user_id: # No user_id could mean system access or all public workplaces
             # For this mock, let's assume if no user_id, return all non-restricted, or handle as per specific app logic
            return [wp for wp_id, wp in MOCK_WORKPLACES_DB.items() if wp_id != "wp4"] # Example: all but restricted
        return [] # Default to no access if user_id not found and is provided

    async def get_workplace_by_id(self, workplace_id: str) -> Optional[Workplace]:
        return MOCK_WORKPLACES_DB.get(workplace_id)
