import pytest
from unittest.mock import MagicMock, patch, AsyncMock 
import json

from app.infrastructure.services.memcached_cache_service import MemcachedCacheService
# from app.core.ports.cache_port import CachePort

@pytest.fixture
def memcached_cache_service_instance(): # Renamed
    with patch('pymemcache.client.base.Client') as mock_pymemcache_client_constructor:
        mock_client_instance = MagicMock()
        mock_pymemcache_client_constructor.return_value = mock_client_instance
        
        service = MemcachedCacheService(server_address="mock-memcached", port=11211)
        yield service, mock_client_instance

@pytest.mark.asyncio
async def test_memcached_get_hit_str(memcached_cache_service_instance):
    service, mock_client = memcached_cache_service_instance
    mock_client.get.return_value = b"cached_value_str"
    result = await service.get("mykey")
    mock_client.get.assert_called_once_with("mykey")
    assert result == "cached_value_str"

@pytest.mark.asyncio
async def test_memcached_get_hit_json(memcached_cache_service_instance):
    service, mock_client = memcached_cache_service_instance
    original_dict = {"data": "value", "number": 123}
    mock_client.get.return_value = json.dumps(original_dict).encode('utf-8')
    result = await service.get("mykey_json")
    mock_client.get.assert_called_once_with("mykey_json")
    assert result == original_dict

@pytest.mark.asyncio
async def test_memcached_get_miss(memcached_cache_service_instance):
    service, mock_client = memcached_cache_service_instance
    mock_client.get.return_value = None
    result = await service.get("mykey_miss")
    mock_client.get.assert_called_once_with("mykey_miss")
    assert result is None

@pytest.mark.asyncio
async def test_memcached_set_str(memcached_cache_service_instance):
    service, mock_client = memcached_cache_service_instance
    await service.set("mykey_set", "new_value", expire=3600)
    mock_client.set.assert_called_once_with("mykey_set", b"new_value", expire=3600)

@pytest.mark.asyncio
async def test_memcached_set_json(memcached_cache_service_instance):
    service, mock_client = memcached_cache_service_instance
    data_to_set = {"complex": [1,2,"three"]}
    await service.set("mykey_set_json", data_to_set, expire=60)
    mock_client.set.assert_called_once_with("mykey_set_json", json.dumps(data_to_set).encode('utf-8'), expire=60)


@pytest.mark.asyncio
async def test_memcached_set_no_expire(memcached_cache_service_instance):
    service, mock_client = memcached_cache_service_instance
    await service.set("mykey_set_no_expire", "another_value") # Default expire=0 for pymemcache
    mock_client.set.assert_called_once_with("mykey_set_no_expire", b"another_value", expire=0)

@pytest.mark.asyncio
async def test_memcached_delete(memcached_cache_service_instance):
    service, mock_client = memcached_cache_service_instance
    await service.delete("mykey_del")
    mock_client.delete.assert_called_once_with("mykey_del")

@pytest.mark.asyncio
async def test_memcached_exists_true(memcached_cache_service_instance):
    service, mock_client = memcached_cache_service_instance
    mock_client.get.return_value = b"something" # Exists if get returns anything
    result = await service.exists("mykey_exists")
    mock_client.get.assert_called_once_with("mykey_exists")
    assert result is True

@pytest.mark.asyncio
async def test_memcached_exists_false(memcached_cache_service_instance):
    service, mock_client = memcached_cache_service_instance
    mock_client.get.return_value = None
    result = await service.exists("mykey_not_exists")
    mock_client.get.assert_called_once_with("mykey_not_exists")
    assert result is False

# Pymemcache client is sync, connect/disconnect are not typically async operations in the same way
# as redis.asyncio. If connect/disconnect methods were added to the service, they'd need testing.
# For now, the client is created in __init__.
