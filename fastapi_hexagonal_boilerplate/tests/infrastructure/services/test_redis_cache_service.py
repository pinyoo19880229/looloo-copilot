import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.infrastructure.services.redis_cache_service import RedisCacheService
# from app.core.ports.cache_port import CachePort # Already in fixture file

# Fixture from previous step (ensure it's in the same file or imported)
@pytest.fixture
async def redis_cache_service_instance(): # Renamed to avoid conflict if running this script directly
    with patch('redis.asyncio.from_url') as mock_from_url:
        mock_redis_client = AsyncMock()
        mock_from_url.return_value = mock_redis_client
        
        service = RedisCacheService(redis_url="redis://mock-redis:6379")
        service.client = mock_redis_client 
        mock_redis_client.ping = AsyncMock(return_value=True) # For connect method if called
        # yield service # if service.connect() is called
        # For this structure, let's assume client is directly set
        yield service, mock_redis_client # also return client for direct mock assertions

@pytest.mark.asyncio
async def test_redis_cache_get_hit(redis_cache_service_instance):
    service, mock_client = redis_cache_service_instance
    mock_client.get.return_value = "cached_value"
    result = await service.get("mykey")
    mock_client.get.assert_called_once_with("mykey")
    assert result == "cached_value"

@pytest.mark.asyncio
async def test_redis_cache_get_miss(redis_cache_service_instance):
    service, mock_client = redis_cache_service_instance
    mock_client.get.return_value = None
    result = await service.get("mykey_miss")
    mock_client.get.assert_called_once_with("mykey_miss")
    assert result is None

@pytest.mark.asyncio
async def test_redis_cache_set(redis_cache_service_instance):
    service, mock_client = redis_cache_service_instance
    await service.set("mykey_set", "new_value", expire=3600)
    mock_client.set.assert_called_once_with("mykey_set", "new_value", ex=3600)

@pytest.mark.asyncio
async def test_redis_cache_set_no_expire(redis_cache_service_instance):
    service, mock_client = redis_cache_service_instance
    await service.set("mykey_set_no_expire", "another_value")
    mock_client.set.assert_called_once_with("mykey_set_no_expire", "another_value", ex=None)

@pytest.mark.asyncio
async def test_redis_cache_delete(redis_cache_service_instance):
    service, mock_client = redis_cache_service_instance
    await service.delete("mykey_del")
    mock_client.delete.assert_called_once_with("mykey_del")

@pytest.mark.asyncio
async def test_redis_cache_exists_true(redis_cache_service_instance):
    service, mock_client = redis_cache_service_instance
    mock_client.exists.return_value = 1 # Redis client returns count of existing keys
    result = await service.exists("mykey_exists")
    mock_client.exists.assert_called_once_with("mykey_exists")
    assert result is True

@pytest.mark.asyncio
async def test_redis_cache_exists_false(redis_cache_service_instance):
    service, mock_client = redis_cache_service_instance
    mock_client.exists.return_value = 0
    result = await service.exists("mykey_not_exists")
    mock_client.exists.assert_called_once_with("mykey_not_exists")
    assert result is False

@pytest.mark.asyncio
async def test_redis_cache_connect_disconnect(redis_cache_service_instance):
    service, mock_client = redis_cache_service_instance
    # Connect is implicitly tested by fixture setup if client is set
    # Test explicit connect call
    await service.connect() # Should use the mocked from_url and set up client
    mock_client.ping.assert_called_once() # Assuming connect calls ping

    # Test disconnect
    await service.disconnect()
    mock_client.close.assert_called_once()
    assert service.client is None

@pytest.mark.asyncio
async def test_redis_cache_operations_no_client(redis_cache_service_instance):
    service, _ = redis_cache_service_instance # We get the service
    service.client = None # Simulate disconnected client
    
    assert await service.get("key") is None
    await service.set("key", "value") # Should not raise, but also not call mock if client is None
    await service.delete("key")
    assert await service.exists("key") is False
    # Add assertions here that mock_client methods were NOT called if that's the desired behavior
    # For instance, if service.client.get was mocked, check call_count == 0
