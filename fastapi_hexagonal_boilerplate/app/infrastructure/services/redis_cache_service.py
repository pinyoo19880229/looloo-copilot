import redis.asyncio as redis
from typing import Any, Optional

from app.core.ports.cache_port import CachePort

class RedisCacheService(CachePort):
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.client = None

    async def connect(self):
        # Use from_url to handle connection pooling and simpler setup
        self.client = redis.from_url(self.redis_url, encoding="utf-8", decode_responses=True)
        try:
            await self.client.ping()
            print("Successfully connected to Redis.")
        except Exception as e:
            print(f"Failed to connect to Redis: {e}")
            self.client = None # Ensure client is None if connection fails

    async def disconnect(self):
        if self.client:
            await self.client.close()
            self.client = None
            print("Disconnected from Redis.")

    async def get(self, key: str) -> Optional[Any]:
        if not self.client:
            # Or raise an exception, depending on desired behavior
            print("Redis client not connected.")
            return None
        return await self.client.get(key)

    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> None:
        if not self.client:
            print("Redis client not connected.")
            return
        await self.client.set(key, value, ex=expire)

    async def delete(self, key: str) -> None:
        if not self.client:
            print("Redis client not connected.")
            return
        await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        if not self.client:
            print("Redis client not connected.")
            return False
        return bool(await self.client.exists(key))

# Example usage (optional, for testing or direct use)
# async def main():
#     cache_service = RedisCacheService(redis_url="redis://localhost:6379/0")
#     await cache_service.connect()
#     if cache_service.client: # Check if connection was successful
#         await cache_service.set("mykey", "myvalue", expire=60)
#         print(f"Value for 'mykey': {await cache_service.get('mykey')}")
#         print(f"Does 'mykey' exist? {await cache_service.exists('mykey')}")
#         await cache_service.delete("mykey")
#         print(f"Does 'mykey' exist after deletion? {await cache_service.exists('mykey')}")
#         await cache_service.disconnect()
# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())
