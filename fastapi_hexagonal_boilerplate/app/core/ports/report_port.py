from abc import ABC, abstractmethod
from typing import Any, Dict
from app.core.models.report import ReportRequestParams

class ReportPort(ABC):
    """
    Port for generating specific report data.
    """

    @abstractmethod
    async def generate_report_data(
        self, 
        report_key: str,
        params: ReportRequestParams,
        # accessible_workplace_ids: List[str] # Might be passed by use case after filtering
    ) -> Any: # Could be List[Dict], pd.DataFrame, etc.
        """
        Generates data for a specific report_key based on the request parameters.
        The structure of the returned data will depend on the report type.
        It's expected that the implementation of this port handles data fetching
        and processing for the given report_key.
        
        'accessible_workplace_ids' could be provided by the use case to ensure
        the adapter only fetches data for authorized workplaces.
        """
        pass
