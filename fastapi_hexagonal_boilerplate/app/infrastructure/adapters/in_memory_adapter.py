import asyncio 
from typing import Any, List, Dict, Optional
import uuid 
import copy # For returning copies of records to avoid external modification

from app.core.ports.database_port import DatabasePort

class InMemoryAdapter(DatabasePort):
    def __init__(self):
        self._data: Dict[str, List[Dict[str, Any]]] = {} 
        self._lock = asyncio.Lock() 

    async def connect(self) -> None:
        print("In-memory database connected (no actual connection required).")
        pass

    async def disconnect(self) -> None:
        print("In-memory database disconnected (no actual disconnection required).")
        pass

    async def insert(self, collection: str, data: Dict[str, Any]) -> Any:
        async with self._lock:
            if collection not in self._data:
                self._data[collection] = []
            
            new_id = data.get("_id") or data.get("id") or str(uuid.uuid4())
            # Create a copy to store, ensuring internal data is not the same object as input `data`
            record_to_store = copy.deepcopy(data)
            record_to_store["_id"] = new_id # Standardize on _id internally for simplicity
            if "id" in record_to_store and record_to_store["id"] != new_id : # if id was there and different, remove it to avoid confusion
                pass # or ensure 'id' and '_id' are consistent if that's a requirement
            elif "id" not in record_to_store: # if 'id' was not in original data, also add 'id' field for consistency with some ORMs/expectations
                 record_to_store["id"] = new_id


            self._data[collection].append(record_to_store)
            return new_id 

    def _matches_query(self, record: Dict[str, Any], query: Dict[str, Any]) -> bool:
        for key, value in query.items():
            # Handle nested queries or operators if needed, e.g. query = {"age": {"$gt": 25}}
            # This basic version only handles direct equality.
            if record.get(key) != value:
                return False
        return True

    async def find_one(self, collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        async with self._lock:
            if collection not in self._data:
                return None
            for record in self._data[collection]:
                if self._matches_query(record, query):
                    return copy.deepcopy(record) # Return a copy
            return None

    async def find_many(self, collection: str, query: Dict[str, Any], limit: int = 0) -> List[Dict[str, Any]]:
        async with self._lock:
            if collection not in self._data:
                return []
            
            results = []
            for record in self._data[collection]:
                if self._matches_query(record, query):
                    results.append(copy.deepcopy(record)) 
                    if limit > 0 and len(results) >= limit:
                        break
            return results

    async def update_one(self, collection: str, query: Dict[str, Any], data: Dict[str, Any]) -> bool:
        async with self._lock:
            if collection not in self._data:
                return False
            
            # data here is expected to be the fields to set, not MongoDB style {'$set': {...}}
            # For a more robust adapter, you might want to handle MongoDB-like update operators.
            for i, record in enumerate(self._data[collection]):
                if self._matches_query(record, query):
                    # Create a new dictionary for the updated record to avoid modifying the list item directly during iteration (though lock helps)
                    updated_record = copy.deepcopy(record)
                    updated_record.update(data) # Merge/overwrite fields
                    self._data[collection][i] = updated_record
                    return True # Update only the first match
            return False

    async def update_many(self, collection: str, query: Dict[str, Any], data: Dict[str, Any]) -> int:
        async with self._lock:
            if collection not in self._data:
                return 0
            
            count = 0
            for i, record in enumerate(self._data[collection]):
                if self._matches_query(record, query):
                    updated_record = copy.deepcopy(record)
                    updated_record.update(data)
                    self._data[collection][i] = updated_record
                    count += 1
            return count

    async def delete_one(self, collection: str, query: Dict[str, Any]) -> bool:
        async with self._lock:
            if collection not in self._data:
                return False
            
            for i, record in enumerate(self._data[collection]):
                if self._matches_query(record, query):
                    del self._data[collection][i]
                    return True 
            return False

    async def delete_many(self, collection: str, query: Dict[str, Any]) -> int:
        async with self._lock:
            if collection not in self._data:
                return 0
            
            initial_len = len(self._data[collection])
            # Rebuild list, excluding records that match the query
            self._data[collection] = [
                record for record in self._data[collection] if not self._matches_query(record, query)
            ]
            return initial_len - len(self._data[collection])
