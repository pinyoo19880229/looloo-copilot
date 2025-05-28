import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pymongo.errors import OperationFailure, ConnectionFailure
from bson import ObjectId # For testing ID types if necessary

from app.infrastructure.adapters.mongodb_adapter import MongoDBAdapter
# from app.core.ports.database_port import DatabasePort

@pytest.fixture
async def mongodb_adapter_instance(): # Renamed
    with patch('motor.motor_asyncio.AsyncIOMotorClient') as mock_motor_constructor:
        mock_client_instance = AsyncMock()
        mock_db_instance = AsyncMock()
        mock_collection_instance = AsyncMock()

        mock_client_instance.__getitem__.return_value = mock_db_instance # client[db_name]
        mock_db_instance.__getitem__.return_value = mock_collection_instance # db[collection_name]
        
        mock_client_instance.admin.command = AsyncMock(return_value=True) # For ping in connect
        mock_motor_constructor.return_value = mock_client_instance
        
        adapter = MongoDBAdapter(mongo_uri="mongodb://mock-mongo:27017", database_name="testdb")
        # Simulate connect()
        adapter.client = mock_client_instance
        adapter.db = mock_db_instance
        
        yield adapter, mock_collection_instance # Return collection mock for assertions

@pytest.mark.asyncio
async def test_mongo_connect_success(mongodb_adapter_instance):
    adapter, _ = mongodb_adapter_instance
    # Fixture already simulates a successful connection by setting client and db
    # If connect() was to be tested explicitly:
    # with patch('motor.motor_asyncio.AsyncIOMotorClient') as mc:
    #    m_client = AsyncMock(); m_client.admin.command = AsyncMock(return_value=True); mc.return_value = m_client
    #    adapter_to_connect = MongoDBAdapter(mongo_uri="uri", database_name="db")
    #    await adapter_to_connect.connect()
    #    assert adapter_to_connect.client is not None
    #    m_client.admin.command.assert_called_with('ping')
    assert adapter.client is not None
    assert adapter.db is not None


@pytest.mark.asyncio
async def test_mongo_connect_fail(mongodb_adapter_instance): # adapter_instance provides a *successful* mock
    # To test failure, we need to make the mock raise an error
    with patch('motor.motor_asyncio.AsyncIOMotorClient') as mock_motor_constructor_fail:
        mock_client_instance_fail = AsyncMock()
        mock_client_instance_fail.admin.command = AsyncMock(side_effect=ConnectionFailure("Ping failed"))
        mock_motor_constructor_fail.return_value = mock_client_instance_fail

        adapter_fail = MongoDBAdapter(mongo_uri="mongodb://mock-mongo-fail:27017", database_name="testdb_fail")
        with pytest.raises(ConnectionFailure):
            await adapter_fail.connect()
        assert adapter_fail.client is None
        assert adapter_fail.db is None


@pytest.mark.asyncio
async def test_mongo_disconnect(mongodb_adapter_instance):
    adapter, _ = mongodb_adapter_instance
    mock_client = adapter.client # Get the mock client from the adapter
    
    await adapter.disconnect()
    
    mock_client.close.assert_called_once()
    assert adapter.client is None
    assert adapter.db is None


@pytest.mark.asyncio
async def test_mongo_insert_success(mongodb_adapter_instance):
    adapter, mock_collection = mongodb_adapter_instance
    doc_to_insert = {"name": "test_item", "value": 123}
    mock_insert_result = AsyncMock()
    mock_insert_result.inserted_id = ObjectId() # Simulate ObjectId
    mock_collection.insert_one.return_value = mock_insert_result
    
    inserted_id = await adapter.insert("my_collection", doc_to_insert)
    
    mock_collection.insert_one.assert_called_once_with(doc_to_insert)
    assert inserted_id == mock_insert_result.inserted_id

@pytest.mark.asyncio
async def test_mongo_insert_fail(mongodb_adapter_instance):
    adapter, mock_collection = mongodb_adapter_instance
    mock_collection.insert_one.side_effect = OperationFailure("Insert failed")
    
    with pytest.raises(OperationFailure):
        await adapter.insert("my_collection", {"name": "fail_item"})

@pytest.mark.asyncio
async def test_mongo_find_one_success(mongodb_adapter_instance):
    adapter, mock_collection = mongodb_adapter_instance
    query = {"name": "find_me"}
    expected_doc = {"_id": ObjectId(), "name": "find_me", "value": 456}
    mock_collection.find_one.return_value = expected_doc
    
    result = await adapter.find_one("my_collection", query)
    
    mock_collection.find_one.assert_called_once_with(query)
    assert result == expected_doc

@pytest.mark.asyncio
async def test_mongo_find_one_not_found(mongodb_adapter_instance):
    adapter, mock_collection = mongodb_adapter_instance
    mock_collection.find_one.return_value = None
    result = await adapter.find_one("my_collection", {"name": "not_found"})
    assert result is None

@pytest.mark.asyncio
async def test_mongo_find_many_success(mongodb_adapter_instance):
    adapter, mock_collection = mongodb_adapter_instance
    query = {"category": "A"}
    docs = [{"_id": ObjectId(), "name": "item1"}, {"_id": ObjectId(), "name": "item2"}]
    
    # Mock the cursor and its to_list method
    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=docs)
    mock_collection.find.return_value = mock_cursor
    
    result = await adapter.find_many("my_collection", query, limit=5)
    
    mock_collection.find.assert_called_once_with(query)
    mock_cursor.limit.assert_called_once_with(5)
    mock_cursor.to_list.assert_called_once_with(length=5)
    assert result == docs

@pytest.mark.asyncio
async def test_mongo_update_one_success(mongodb_adapter_instance):
    adapter, mock_collection = mongodb_adapter_instance
    query = {"name": "to_update"}
    update_data = {"$set": {"value": 789}}
    mock_update_result = AsyncMock()
    mock_update_result.modified_count = 1
    mock_collection.update_one.return_value = mock_update_result
    
    updated = await adapter.update_one("my_collection", query, update_data)
    
    mock_collection.update_one.assert_called_once_with(query, update_data)
    assert updated is True

@pytest.mark.asyncio
async def test_mongo_update_one_not_modified(mongodb_adapter_instance):
    adapter, mock_collection = mongodb_adapter_instance
    mock_update_result = AsyncMock()
    mock_update_result.modified_count = 0
    mock_collection.update_one.return_value = mock_update_result
    
    updated = await adapter.update_one("my_collection", {"name": "no_match"}, {"$set": {"value": 0}})
    assert updated is False

@pytest.mark.asyncio
async def test_mongo_update_many_success(mongodb_adapter_instance):
    adapter, mock_collection = mongodb_adapter_instance
    query = {"category": "B"}
    update_data = {"$set": {"status": "updated"}}
    mock_update_result = AsyncMock()
    mock_update_result.modified_count = 3
    mock_collection.update_many.return_value = mock_update_result
    
    count = await adapter.update_many("my_collection", query, update_data)
    
    mock_collection.update_many.assert_called_once_with(query, update_data)
    assert count == 3

@pytest.mark.asyncio
async def test_mongo_delete_one_success(mongodb_adapter_instance):
    adapter, mock_collection = mongodb_adapter_instance
    query = {"name": "to_delete"}
    mock_delete_result = AsyncMock()
    mock_delete_result.deleted_count = 1
    mock_collection.delete_one.return_value = mock_delete_result
    
    deleted = await adapter.delete_one("my_collection", query)
    
    mock_collection.delete_one.assert_called_once_with(query)
    assert deleted is True

@pytest.mark.asyncio
async def test_mongo_delete_many_success(mongodb_adapter_instance):
    adapter, mock_collection = mongodb_adapter_instance
    query = {"category": "C"}
    mock_delete_result = AsyncMock()
    mock_delete_result.deleted_count = 5
    mock_collection.delete_many.return_value = mock_delete_result
    
    count = await adapter.delete_many("my_collection", query)
    
    mock_collection.delete_many.assert_called_once_with(query)
    assert count == 5

@pytest.mark.asyncio
async def test_mongo_operations_no_db_connection(mongodb_adapter_instance):
    adapter, _ = mongodb_adapter_instance
    adapter.db = None # Simulate disconnected
    
    with pytest.raises(ConnectionError, match="Database not connected"):
        await adapter.insert("coll", {"data":1})
    with pytest.raises(ConnectionError):
        await adapter.find_one("coll", {"data":1})
    # ... and so on for other methods
