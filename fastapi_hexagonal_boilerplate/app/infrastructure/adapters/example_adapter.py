from app.core.ports.example_port import ExampleServicePort

class ExampleServiceAdapter(ExampleServicePort):
    """
    An adapter that implements the ExampleServicePort.
    This adapter might interact with a database, an external API, or another service.
    For this example, it returns a simple dictionary.
    """

    def get_some_data(self, item_id: str) -> dict:
        """
        Concrete implementation of the get_some_data method.
        """
        # In a real scenario, this method would interact with an external system,
        # a database, or another microservice.
        return {
            "id": item_id,
            "data": f"Data for item {item_id} from ExampleServiceAdapter",
            "source": "ExampleServiceAdapter"
        }

# Example Usage (illustrative)
if __name__ == "__main__":
    adapter = ExampleServiceAdapter()
    data = adapter.get_some_data("test_item_123")
    print(data)
