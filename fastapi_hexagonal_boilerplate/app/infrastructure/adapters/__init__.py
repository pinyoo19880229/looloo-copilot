# fastapi_hexagonal_boilerplate/app/infrastructure/adapters/__init__.py
from .mock_workplace_adapter import MockWorkplaceAdapter
from .mock_report_adapter import MockReportAdapter
from .mongodb_adapter import MongoDBAdapter
from .postgresql_adapter import PostgreSQLAdapter
from .in_memory_adapter import InMemoryAdapter

# Attempt to import ExampleServiceAdapter if it exists, otherwise ignore.
# This handles cases where it might have been removed or is part of a different setup.
try:
    from .example_adapter import ExampleServiceAdapter
    __all__ = [
        "ExampleServiceAdapter",
        "MockWorkplaceAdapter",
        "MockReportAdapter",
        "MongoDBAdapter",
        "PostgreSQLAdapter",
        "InMemoryAdapter",
    ]
except ImportError:
    __all__ = [
        "MockWorkplaceAdapter",
        "MockReportAdapter",
        "MongoDBAdapter",
        "PostgreSQLAdapter",
        "InMemoryAdapter",
    ]
