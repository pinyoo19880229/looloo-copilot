# Assuming example_adapter.py might still be there or removed.
from .example_adapter import ExampleServiceAdapter 

from .mock_workplace_adapter import MockWorkplaceAdapter
from .mock_report_adapter import MockReportAdapter

__all__ = [
    "ExampleServiceAdapter", # Kept as example_adapter.py exists
    "MockWorkplaceAdapter",
    "MockReportAdapter",
]
