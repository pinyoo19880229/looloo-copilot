import pybreaker
import time # Added for the __main__ block
from app.infrastructure.services.example_service import ExampleExternalService, ExternalServiceError

# Initialize the circuit breaker
# Allow 2 failures within a 60 second window before opening the circuit
# Reset timeout is 30 seconds (how long to wait before going to half-open state)
service_breaker = pybreaker.CircuitBreaker(fail_max=2, reset_timeout=30)

class GetDataUseCase:
    def __init__(self, external_service: ExampleExternalService):
        self.external_service = external_service

    @service_breaker
    def execute(self) -> dict:
        """
        Executes the use case to get data, with circuit breaker protection.
        """
        try:
            # This call is protected by the circuit breaker
            data = self.external_service.get_data()
            return data
        except ExternalServiceError as e:
            # Handle specific service error, possibly re-raising or returning a default
            # The circuit breaker will also count this as a failure.
            raise  # Re-raise for now, or handle appropriately
        except pybreaker.CircuitBreakerError as e:
            # This exception is raised when the circuit is open
            # Handle it by returning a default response or raising a specific app error
            return {"error": "Service is currently unavailable. Please try again later.", "details": str(e)}

# Example Usage (illustrative)
if __name__ == "__main__":
    # This is just for demonstration if you run this file directly.
    # In a real app, dependencies would be injected.
    service = ExampleExternalService(fail_rate=0.6) 
    use_case = GetDataUseCase(external_service=service)

    for i in range(10):
        print(f"Use Case Attempt {i+1}:")
        result = use_case.execute()
        print(result)
        if "error" in result and "Service is currently unavailable" in result.get("error", ""): # Make .get more robust
            print("Circuit is OPEN. Waiting for it to potentially close...")
            time.sleep(5) # Wait a bit before retrying to see state changes
        elif "error" not in result:
             # Successful call, reset fail_rate to see breaker close faster in demo
            service.fail_rate = 0.1 
        print("-" * 20)
