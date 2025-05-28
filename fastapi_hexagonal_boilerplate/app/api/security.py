from fastapi import Security, HTTPException, status, Depends
from fastapi.security.api_key import APIKeyHeader, APIKeyQuery, APIKeyCookie # Example sources
import os

# Define where the API key can be passed (e.g., header)
API_KEY_NAME = "X-API-KEY" # Common header name
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False) # auto_error=False to handle manually

# This is a mock/example valid API key. In a real app, store securely and have multiple.
# You could load this from environment variables or a secure store.
VALID_API_KEY = os.getenv("SERVER_API_KEY", "your_secret_api_key_here") 
# It's good practice to have a different key for a "system user" or internal tasks if needed
# For now, one key for simplicity.

async def get_api_key(
    api_key_header_value: str = Security(api_key_header),
    # You could also check query params or cookies:
    # api_key_query: str = Security(APIKeyQuery(name="api_key", auto_error=False)),
    # api_key_cookie: str = Security(APIKeyCookie(name="api_key", auto_error=False)),
) -> str:
    """
    Dependency to validate the API key.
    Checks header, then query, then cookie. (Order can be adjusted)
    Raises HTTPException if no valid key is found.
    """
    # Prioritize header
    if api_key_header_value and api_key_header_value == VALID_API_KEY:
        return api_key_header_value
    
    # Example for checking query or cookie (if you enabled them above)
    # if api_key_query and api_key_query == VALID_API_KEY:
    #     return api_key_query
    # if api_key_cookie and api_key_cookie == VALID_API_KEY:
    #     return api_key_cookie

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )

async def get_current_user_id_from_api_key(
    api_key: str = Depends(get_api_key) # Ensures API key is valid first
) -> str:
    """
    Placeholder dependency to get a 'user_id' associated with an API key.
    In a real system, you would look up the user/entity associated with this key.
    For this mock, we'll return a static user_id if the key is valid.
    """
    if api_key == VALID_API_KEY:
        # This would be a lookup in a real system, e.g., key -> user mapping
        return "user_from_api_key_abc123" 
    
    # This part should ideally not be reached if get_api_key works correctly
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not identify user from API Key",
    )
