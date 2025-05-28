import redis.asyncio as redis
from typing import Optional
import time # For timeout logic if not using blocking_timeout directly in acquire
import asyncio # For asyncio.sleep

from app.core.ports.distributed_lock_port import DistributedLockPort

class RedisDistributedLockService(DistributedLockPort):
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.client = None
        # It's good practice to namespace locks if the Redis instance is shared
        self.lock_prefix = "lock:"

    async def connect(self):
        self.client = redis.from_url(self.redis_url, encoding="utf-8", decode_responses=True)
        try:
            await self.client.ping()
            print("Successfully connected to Redis for Distributed Locking.")
        except Exception as e:
            print(f"Failed to connect to Redis for Distributed Locking: {e}")
            self.client = None

    async def disconnect(self):
        if self.client:
            await self.client.close()
            self.client = None
            print("Disconnected from Redis (Distributed Locking).")

    async def acquire(self, lock_key: str, timeout: int = 10, expire: Optional[int] = 60) -> bool:
        '''
        Acquire a lock.
        :param lock_key: The key for the lock.
        :param timeout: How long to wait (in seconds) to acquire the lock before giving up.
        :param expire: How long (in seconds) the lock should be held before automatically releasing.
                       This is important to prevent deadlocks if a service crashes.
        :return: True if the lock was acquired, False otherwise.
        '''
        if not self.client:
            print("Redis client not connected for locking.")
            return False

        prefixed_lock_key = self.lock_prefix + lock_key
        # If expire is None, Redis `set` command with `nx=True` would set it without expiry.
        # For distributed locks, an expiry (px for milliseconds, ex for seconds) is crucial.
        # Defaulting to 60 seconds if not specified.
        lock_expire_time = expire if expire is not None else 60


        end_time = time.monotonic() + timeout
        while time.monotonic() < end_time:
            # SET key value NX EX expiry_time
            # NX -- Only set the key if it does not already exist.
            # EX -- Set the specified expire time, in seconds.
            # PX -- Set the specified expire time, in milliseconds.
            if await self.client.set(prefixed_lock_key, "locked", nx=True, ex=lock_expire_time):
                return True
            # Wait a short period before retrying to avoid busy-waiting
            # In a real-world scenario, consider a small, increasing backoff.
            await asyncio.sleep(0.01) # Minimal sleep to yield control
        return False

    async def release(self, lock_key: str) -> bool:
        '''
        Release a lock.
        :param lock_key: The key for the lock.
        :return: True if the lock was released, False otherwise (e.g., lock didn't exist).
        '''
        if not self.client:
            print("Redis client not connected for locking.")
            return False
        
        prefixed_lock_key = self.lock_prefix + lock_key
        # Ensure that we only delete the lock if it's still held by us.
        # This is a simplified release. For critical systems, consider Lua scripts
        # to make the get-and-delete atomic to prevent deleting a lock re-acquired by someone else.
        # However, if the lock value is unique to the locker (e.g., a UUID), that can be checked.
        # For this implementation, we assume simple lock/unlock.
        deleted_count = await self.client.delete(prefixed_lock_key)
        return deleted_count > 0

    async def is_locked(self, lock_key: str) -> bool:
        '''
        Check if a lock is currently held.
        :param lock_key: The key for the lock.
        :return: True if the lock exists, False otherwise.
        '''
        if not self.client:
            print("Redis client not connected for locking.")
            return False
        prefixed_lock_key = self.lock_prefix + lock_key
        return bool(await self.client.exists(prefixed_lock_key))

# Example usage (optional)
# async def main():
#     import asyncio
#     lock_service = RedisDistributedLockService(redis_url="redis://localhost:6379/0")
#     await lock_service.connect()

#     if lock_service.client:
#         lock_name = "my_resource_lock"
        
#         print(f"Attempting to acquire lock '{lock_name}'...")
#         if await lock_service.acquire(lock_name, timeout=5, expire=30):
#             print(f"Lock '{lock_name}' acquired.")
#             print(f"Is '{lock_name}' locked? {await lock_service.is_locked(lock_name)}")
            
#             # Simulate work
#             await asyncio.sleep(5) 
            
#             await lock_service.release(lock_name)
#             print(f"Lock '{lock_name}' released.")
#             print(f"Is '{lock_name}' locked after release? {await lock_service.is_locked(lock_name)}")
#         else:
#             print(f"Failed to acquire lock '{lock_name}'.")

#         # Test lock timeout
#         print(f"Attempting to acquire lock '{lock_name}' with short expiry (5s)...")
#         if await lock_service.acquire(lock_name, expire=5):
#             print("Lock acquired. Waiting for it to expire automatically...")
#             await asyncio.sleep(7) # Wait longer than expiry
#             print(f"Is '{lock_name}' locked after auto-expiry? {await lock_service.is_locked(lock_name)}")
#             # Try to release it (should ideally fail or do nothing if already expired)
#             await lock_service.release(lock_name) 
#         else:
#             print("Failed to acquire lock for expiry test.")
        
#         await lock_service.disconnect()

# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())
