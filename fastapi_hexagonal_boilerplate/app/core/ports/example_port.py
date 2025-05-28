from abc import ABC, abstractmethod

class ExampleServicePort(ABC):
    """
    A port defining an operation that the core domain needs.
    This could be for fetching data, sending notifications, etc.
    """

    @abstractmethod
    def get_some_data(self, item_id: str) -> dict:
        """
        Abstract method to get some data based on an item_id.
        Implementations (adapters) will provide the concrete logic.
        """
        pass
