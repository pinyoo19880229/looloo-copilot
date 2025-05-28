import random
import time

class ExternalServiceError(Exception):
    """Custom exception for external service failures."""
    pass

class ExampleExternalService:
    """
    A dummy external service that might fail or be slow.
    """
    def __init__(self, fail_rate: float = 0.5, max_delay: float = 1.0):
        self.fail_rate = fail_rate
        self.max_delay = max_delay

    def get_data(self) -> dict:
        """
        Simulates fetching data from an external service.
        May raise ExternalServiceError or introduce delays.
        """
        # Simulate delay
        time.sleep(random.uniform(0, self.max_delay))

        # Simulate failure
        if random.random() < self.fail_rate:
            raise ExternalServiceError("Simulated failure in external service")
        
        return {"data": "Sample data from external service", "source": "ExampleExternalService"}

# Example usage (not part of the class, just for illustration if run directly)
if __name__ == "__main__":
    service = ExampleExternalService(fail_rate=0.3, max_delay=0.5)
    for i in range(10):
        try:
            print(f"Attempt {i+1}: {service.get_data()}")
        except ExternalServiceError as e:
            print(f"Attempt {i+1}: Error: {e}")
