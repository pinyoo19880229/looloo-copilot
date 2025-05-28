import pytest
import uuid
import copy # For verifying deep copies if necessary

from app.infrastructure.adapters.in_memory_adapter import InMemoryAdapter
# from app.core.ports.database_port import DatabasePort

@pytest.fixture
async def in_memory_adapter_instance(): # Renamed
    adapter = InMemoryAdapter()
    # Connect and disconnect are no-ops but can be called for completeness
    await adapter.connect() 
    yield adapter
    await adapter.disconnect()

@pytest.mark.asyncio
async def test_in_memory_insert_and_find_one(in_memory_adapter_instance):
    adapter = in_memory_adapter_instance
    doc_to_insert = {"name": "InMem Test", "value": 100}
    
    inserted_id = await adapter.insert("test_coll", doc_to_insert)
    assert inserted_id is not None
    
    # Verify _id was added and is same as returned id
    # Also check if 'id' field was added if not present
    found_doc = await adapter.find_one("test_coll", {"_id": inserted_id})
    assert found_doc is not None
    assert found_doc["name"] == "InMem Test"
    assert found_doc["value"] == 100
    assert "_id" in found_doc
    assert "id" in found_doc # As per current InMemoryAdapter insert logic
    assert found_doc["_id"] == inserted_id
    assert found_doc["id"] == inserted_id


    # Test finding by original field
    found_by_name = await adapter.find_one("test_coll", {"name": "InMem Test"})
    assert found_by_name is not None
    assert found_by_name["_id"] == inserted_id

@pytest.mark.asyncio
async def test_in_memory_insert_with_provided_id(in_memory_adapter_instance):
    adapter = in_memory_adapter_instance
    custom_id = "my_custom_id_123"
    doc_to_insert = {"_id": custom_id, "name": "Custom ID Item"}
    
    returned_id = await adapter.insert("test_coll", doc_to_insert)
    assert returned_id == custom_id
    
    found_doc = await adapter.find_one("test_coll", {"_id": custom_id})
    assert found_doc is not None
    assert found_doc["name"] == "Custom ID Item"

@pytest.mark.asyncio
async def test_in_memory_find_one_not_found(in_memory_adapter_instance):
    adapter = in_memory_adapter_instance
    await adapter.insert("test_coll", {"name": "existing"})
    
    found_doc = await adapter.find_one("test_coll", {"name": "non_existent"})
    assert found_doc is None
    
    found_in_other_coll = await adapter.find_one("other_coll", {"name": "existing"})
    assert found_in_other_coll is None


@pytest.mark.asyncio
async def test_in_memory_find_many(in_memory_adapter_instance):
    adapter = in_memory_adapter_instance
    await adapter.insert("test_coll_many", {"name": "item1", "category": "A"})
    await adapter.insert("test_coll_many", {"name": "item2", "category": "B"})
    await adapter.insert("test_coll_many", {"name": "item3", "category": "A"})
    
    results_A = await adapter.find_many("test_coll_many", {"category": "A"})
    assert len(results_A) == 2
    assert all(item["category"] == "A" for item in results_A)
    
    results_B = await adapter.find_many("test_coll_many", {"category": "B"})
    assert len(results_B) == 1
    
    results_all = await adapter.find_many("test_coll_many", {})
    assert len(results_all) == 3

@pytest.mark.asyncio
async def test_in_memory_find_many_with_limit(in_memory_adapter_instance):
    adapter = in_memory_adapter_instance
    for i in range(5):
        await adapter.insert("test_coll_limit", {"name": f"item_{i}", "order": i})
        
    results_limit_2 = await adapter.find_many("test_coll_limit", {}, limit=2)
    assert len(results_limit_2) == 2
    # Check if it returns copies
    results_limit_2[0]["name"] = "MODIFIED" 
    original_still_there = await adapter.find_one("test_coll_limit", {"order": 0})
    assert original_still_there["name"] == "item_0"


@pytest.mark.asyncio
async def test_in_memory_update_one(in_memory_adapter_instance):
    adapter = in_memory_adapter_instance
    doc_id = await adapter.insert("test_coll_update", {"name": "initial_name", "value": 10})
    
    updated = await adapter.update_one("test_coll_update", {"_id": doc_id}, {"value": 20, "status": "updated"})
    assert updated is True
    
    updated_doc = await adapter.find_one("test_coll_update", {"_id": doc_id})
    assert updated_doc["value"] == 20
    assert updated_doc["status"] == "updated"
    assert updated_doc["name"] == "initial_name" # Should not be removed

    not_updated = await adapter.update_one("test_coll_update", {"_id": "non_existent_id"}, {"value": 30})
    assert not_updated is False

@pytest.mark.asyncio
async def test_in_memory_update_many(in_memory_adapter_instance):
    adapter = in_memory_adapter_instance
    await adapter.insert("test_coll_upd_many", {"name": "itemA", "category": "X", "val": 1})
    await adapter.insert("test_coll_upd_many", {"name": "itemB", "category": "Y", "val": 1})
    await adapter.insert("test_coll_upd_many", {"name": "itemC", "category": "X", "val": 1})
    
    count = await adapter.update_many("test_coll_upd_many", {"category": "X"}, {"val": 2, "updated": True})
    assert count == 2
    
    updated_items = await adapter.find_many("test_coll_upd_many", {"category": "X"})
    assert len(updated_items) == 2
    assert all(item["val"] == 2 and item["updated"] is True for item in updated_items)
    
    item_Y = await adapter.find_one("test_coll_upd_many", {"category": "Y"})
    assert item_Y["val"] == 1
    assert "updated" not in item_Y

@pytest.mark.asyncio
async def test_in_memory_delete_one(in_memory_adapter_instance):
    adapter = in_memory_adapter_instance
    doc_id1 = await adapter.insert("test_coll_del", {"name": "to_delete_1"})
    doc_id2 = await adapter.insert("test_coll_del", {"name": "to_keep_1"})
    
    deleted = await adapter.delete_one("test_coll_del", {"_id": doc_id1})
    assert deleted is True
    assert await adapter.find_one("test_coll_del", {"_id": doc_id1}) is None
    assert await adapter.find_one("test_coll_del", {"_id": doc_id2}) is not None

    not_deleted = await adapter.delete_one("test_coll_del", {"_id": "non_existent"})
    assert not_deleted is False

@pytest.mark.asyncio
async def test_in_memory_delete_many(in_memory_adapter_instance):
    adapter = in_memory_adapter_instance
    await adapter.insert("test_coll_del_many", {"name": "del_A1", "category": "A"})
    await adapter.insert("test_coll_del_many", {"name": "del_B1", "category": "B"})
    await adapter.insert("test_coll_del_many", {"name": "del_A2", "category": "A"})
    
    count = await adapter.delete_many("test_coll_del_many", {"category": "A"})
    assert count == 2
    
    remaining_A = await adapter.find_many("test_coll_del_many", {"category": "A"})
    assert len(remaining_A) == 0
    
    remaining_B = await adapter.find_many("test_coll_del_many", {"category": "B"})
    assert len(remaining_B) == 1

@pytest.mark.asyncio
async def test_in_memory_data_isolation(in_memory_adapter_instance):
    adapter = in_memory_adapter_instance
    original_data = {"details": {"level": 1}}
    doc_id = await adapter.insert("test_coll_iso", original_data)
    
    # Test find_one returns a copy
    found_doc = await adapter.find_one("test_coll_iso", {"_id": doc_id})
    found_doc["details"]["level"] = 2 # Modify the copy
    
    re_found_doc = await adapter.find_one("test_coll_iso", {"_id": doc_id})
    assert re_found_doc["details"]["level"] == 1 # Original should be unchanged

    # Test find_many returns copies
    many_docs = await adapter.find_many("test_coll_iso", {"_id": doc_id})
    many_docs[0]["details"]["level"] = 3 # Modify the copy
    
    re_found_doc_again = await adapter.find_one("test_coll_iso", {"_id": doc_id})
    assert re_found_doc_again["details"]["level"] == 1 # Original should be unchanged
