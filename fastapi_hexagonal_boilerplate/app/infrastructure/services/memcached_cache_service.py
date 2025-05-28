from pymemcache.client.base import Client as MemcachedClient
from pymemcache.client.retrying import RetryingClient
from pymemcache.exceptions import MemcacheUnexpectedCloseError
from typing import Any, Optional
import json # For serializing non-string objects

from app.core.ports.cache_port import CachePort

class MemcachedCacheService(CachePort):
    def __init__(self, server_address: str, port: int = 11211):
        # server_address should be like 'localhost' or 'memcached_server_ip'
        self.server_address = server_address
        self.port = port
        # Basic client
        # For production, consider using RetryingClient or a client with connection pooling
        self.client = MemcachedClient((self.server_address, self.port), connect_timeout=5, timeout=5)
        # Example of RetryingClient for more robustness
        # base_client = MemcachedClient((self.server_address, self.port), connect_timeout=5, timeout=5)
        # self.client = RetryingClient(
        #     base_client,
        #     attempts=3,
        #     retry_delay=0.01, # seconds
        #     retry_for=[MemcacheUnexpectedCloseError]
        # )
        print(f"Memcached client initialized for {self.server_address}:{self.port}")

    async def _serialize(self, value: Any) -> bytes:
        if isinstance(value, bytes):
            return value
        elif isinstance(value, str):
            return value.encode('utf-8')
        else:
            # For other types, serialize to JSON string then encode
            return json.dumps(value).encode('utf-8')

    async def _deserialize(self, value: Optional[bytes]) -> Optional[Any]:
        if value is None:
            return None
        try:
            # Try to decode as UTF-8 string first
            decoded_str = value.decode('utf-8')
            try:
                # Then try to parse as JSON
                return json.loads(decoded_str)
            except json.JSONDecodeError:
                # If JSON parsing fails, it's likely a plain string
                return decoded_str
        except UnicodeDecodeError:
            # If UTF-8 decoding fails, return as raw bytes (or handle as error)
            return value


    async def get(self, key: str) -> Optional[Any]:
        # pymemcache is synchronous, so we wrap calls or use a thread pool executor in a real async app
        # For simplicity here, direct calls are shown. Consider `asyncio.to_thread` in a real FastAPI app.
        raw_value = self.client.get(key)
        return await self._deserialize(raw_value)

    async def set(self, key: str, value: Any, expire: Optional[int] = 0) -> None: # expire is in seconds, 0 means forever
        # pymemcache expects expire to be an int. Optional[int] = None from port, default to 0 for pymemcache
        serialized_value = await self._serialize(value)
        self.client.set(key, serialized_value, expire=expire or 0) # Ensure expire is int, 0 for no expiry

    async def delete(self, key: str) -> None:
        self.client.delete(key)

    async def exists(self, key: str) -> bool:
        return self.client.get(key) is not None

    # Optional: connect/disconnect if managing connections explicitly (e.g., with pools)
    # For basic MemcachedClient, connection is often on-demand.
    # async def connect(self):
    #     # With basic client, connection is typically established on first command.
    #     # Ping can be used to check server status.
    #     try:
    #         self.client.version() # A simple command to check connection
    #         print("Successfully connected to Memcached (or verified connection).")
    #     except Exception as e:
    #         print(f"Failed to connect/ping Memcached: {e}")

    # async def disconnect(self):
    #     self.client.close()
    #     print("Disconnected from Memcached.")

# Example usage (optional)
# async def main():
#     # Ensure Memcached server is running (e.g., via Docker: docker run --name my-memcache -p 11211:11211 -d memcached)
#     cache_service = MemcachedCacheService(server_address="localhost", port=11211)
#     # await cache_service.connect() # If explicit connect is implemented
    
#     await cache_service.set("mykey_mc", {"name": "test_user", "id": 123}, expire=60)
#     retrieved_value = await cache_service.get("mykey_mc")
#     print(f"Value for 'mykey_mc': {retrieved_value}")
#     print(f"Does 'mykey_mc' exist? {await cache_service.exists('mykey_mc')}")
    
#     await cache_service.delete("mykey_mc")
#     print(f"Does 'mykey_mc' exist after deletion? {await cache_service.exists('mykey_mc')}")
    
#     # await cache_service.disconnect() # If explicit disconnect is implemented

# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())
