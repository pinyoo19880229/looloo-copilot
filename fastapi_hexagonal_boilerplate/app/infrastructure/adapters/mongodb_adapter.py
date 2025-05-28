from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Any, List, Dict, Optional
from pymongo.errors import ConnectionFailure, OperationFailure # For error handling
import asyncio # Required for explicit loop management if needed, good practice for async libraries

from app.core.ports.database_port import DatabasePort

class MongoDBAdapter(DatabasePort):
    def __init__(self, mongo_uri: str, database_name: str):
        self.mongo_uri = mongo_uri
        self.database_name = database_name
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None

    async def connect(self) -> None:
        if not self.client:
            try:
                # motor uses the current event loop by default.
                self.client = AsyncIOMotorClient(self.mongo_uri)
                # Verify connection by trying to access server info
                await self.client.admin.command('ping') 
                self.db = self.client[self.database_name]
                print(f"Successfully connected to MongoDB: {self.mongo_uri}, Database: {self.database_name}")
            except ConnectionFailure as e:
                print(f"MongoDB connection failed: {e}")
                self.client = None
                self.db = None
                # Potentially re-raise or handle as per application's error policy
                raise

    async def disconnect(self) -> None:
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            print("Disconnected from MongoDB.")

    async def insert(self, collection: str, data: Dict[str, Any]) -> Any:
        if not self.db:
            raise ConnectionError("Database not connected. Call connect() first.")
        try:
            result = await self.db[collection].insert_one(data)
            return result.inserted_id
        except OperationFailure as e:
            print(f"MongoDB insert operation failed: {e}")
            raise 

    async def find_one(self, collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.db:
            raise ConnectionError("Database not connected. Call connect() first.")
        try:
            return await self.db[collection].find_one(query)
        except OperationFailure as e:
            print(f"MongoDB find_one operation failed: {e}")
            raise

    async def find_many(self, collection: str, query: Dict[str, Any], limit: int = 0) -> List[Dict[str, Any]]:
        if not self.db:
            raise ConnectionError("Database not connected. Call connect() first.")
        try:
            cursor = self.db[collection].find(query)
            if limit > 0:
                cursor = cursor.limit(limit)
            # Pass length to to_list for efficient fetching, None means all documents
            return await cursor.to_list(length=limit if limit > 0 else None) 
        except OperationFailure as e:
            print(f"MongoDB find_many operation failed: {e}")
            raise

    async def update_one(self, collection: str, query: Dict[str, Any], data: Dict[str, Any]) -> bool:
        if not self.db:
            raise ConnectionError("Database not connected. Call connect() first.")
        try:
            # Ensure '$set' or other MongoDB update operators are used in 'data' for partial updates
            # For simplicity, assuming 'data' is a valid update document (e.g., {'$set': {...}})
            result = await self.db[collection].update_one(query, data)
            return result.modified_count > 0
        except OperationFailure as e:
            print(f"MongoDB update_one operation failed: {e}")
            raise

    async def update_many(self, collection: str, query: Dict[str, Any], data: Dict[str, Any]) -> int:
        if not self.db:
            raise ConnectionError("Database not connected. Call connect() first.")
        try:
            result = await self.db[collection].update_many(query, data)
            return result.modified_count
        except OperationFailure as e:
            print(f"MongoDB update_many operation failed: {e}")
            raise

    async def delete_one(self, collection: str, query: Dict[str, Any]) -> bool:
        if not self.db:
            raise ConnectionError("Database not connected. Call connect() first.")
        try:
            result = await self.db[collection].delete_one(query)
            return result.deleted_count > 0
        except OperationFailure as e:
            print(f"MongoDB delete_one operation failed: {e}")
            raise

    async def delete_many(self, collection: str, query: Dict[str, Any]) -> int:
        if not self.db:
            raise ConnectionError("Database not connected. Call connect() first.")
        try:
            result = await self.db[collection].delete_many(query)
            return result.deleted_count
        except OperationFailure as e:
            print(f"MongoDB delete_many operation failed: {e}")
            raise
