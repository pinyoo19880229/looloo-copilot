import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from app.infrastructure.services.redis_distributed_lock_service import RedisDistributedLockService
# from app.core.ports.distributed_lock_port import DistributedLockPort

@pytest.fixture
async def redis_lock_service_instance(): # Renamed
    with patch('redis.asyncio.from_url') as mock_from_url, \
         patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep: # Mock sleep to speed up tests
        mock_redis_client = AsyncMock()
        mock_from_url.return_value = mock_redis_client
        
        service = RedisDistributedLockService(redis_url="redis://mock-redis:6379")
        service.client = mock_redis_client
        mock_redis_client.ping = AsyncMock(return_value=True)
        
        yield service, mock_redis_client, mock_sleep


@pytest.mark.asyncio
async def test_lock_acquire_success(redis_lock_service_instance):
    service, mock_client, _ = redis_lock_service_instance
    mock_client.set.return_value = True # Simulate successful SET NX EX
    
    lock_key = "my_resource_lock"
    acquired = await service.acquire(lock_key, timeout=1, expire=30)
    
    assert acquired is True
    mock_client.set.assert_called_once_with(f"lock:{lock_key}", "locked", nx=True, ex=30)

@pytest.mark.asyncio
async def test_lock_acquire_fail_timeout(redis_lock_service_instance):
    service, mock_client, mock_sleep = redis_lock_service_instance
    mock_client.set.return_value = False # Simulate lock already taken
    
    lock_key = "my_resource_lock_fail"
    acquired = await service.acquire(lock_key, timeout=0.02, expire=30) # Short timeout
    
    assert acquired is False
    # SET should be called multiple times due to retry loop
    assert mock_client.set.call_count > 0 
    mock_sleep.assert_called() # asyncio.sleep should have been called

@pytest.mark.asyncio
async def test_lock_release_success(redis_lock_service_instance):
    service, mock_client, _ = redis_lock_service_instance
    mock_client.delete.return_value = 1 # Simulate successful deletion
    
    lock_key = "my_resource_lock_release"
    released = await service.release(lock_key)
    
    assert released is True
    mock_client.delete.assert_called_once_with(f"lock:{lock_key}")

@pytest.mark.asyncio
async def test_lock_release_fail(redis_lock_service_instance):
    service, mock_client, _ = redis_lock_service_instance
    mock_client.delete.return_value = 0 # Simulate lock not found or not deleted
    
    lock_key = "my_resource_lock_release_fail"
    released = await service.release(lock_key)
    
    assert released is False
    mock_client.delete.assert_called_once_with(f"lock:{lock_key}")

@pytest.mark.asyncio
async def test_is_locked_true(redis_lock_service_instance):
    service, mock_client, _ = redis_lock_service_instance
    mock_client.exists.return_value = 1
    
    lock_key = "check_lock_taken"
    is_locked = await service.is_locked(lock_key)
    
    assert is_locked is True
    mock_client.exists.assert_called_once_with(f"lock:{lock_key}")

@pytest.mark.asyncio
async def test_is_locked_false(redis_lock_service_instance):
    service, mock_client, _ = redis_lock_service_instance
    mock_client.exists.return_value = 0
    
    lock_key = "check_lock_free"
    is_locked = await service.is_locked(lock_key)
    
    assert is_locked is False
    mock_client.exists.assert_called_once_with(f"lock:{lock_key}")

@pytest.mark.asyncio
async def test_lock_operations_no_client(redis_lock_service_instance):
    service, _, _ = redis_lock_service_instance
    service.client = None # Simulate disconnected
    
    assert await service.acquire("key") is False
    assert await service.release("key") is False
    assert await service.is_locked("key") is False

@pytest.mark.asyncio
async def test_lock_acquire_with_custom_expire(redis_lock_service_instance):
    service, mock_client, _ = redis_lock_service_instance
    mock_client.set.return_value = True
    
    lock_key = "custom_expire_lock"
    await service.acquire(lock_key, expire=120) # Custom expire time
    
    mock_client.set.assert_called_once_with(f"lock:{lock_key}", "locked", nx=True, ex=120)

@pytest.mark.asyncio
async def test_lock_acquire_default_expire(redis_lock_service_instance):
    service, mock_client, _ = redis_lock_service_instance
    mock_client.set.return_value = True
    
    lock_key = "default_expire_lock"
    await service.acquire(lock_key) # Default expire time (should be 60s as per implementation)
    
    mock_client.set.assert_called_once_with(f"lock:{lock_key}", "locked", nx=True, ex=60)
