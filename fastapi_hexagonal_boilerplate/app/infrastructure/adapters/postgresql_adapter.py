import asyncpg # Preferred for asyncio
from typing import Any, List, Dict, Optional

from app.core.ports.database_port import DatabasePort

class PostgreSQLAdapter(DatabasePort):
    def __init__(self, dsn: str): # dsn format: "postgresql://user:pass@host:port/database"
        self.dsn = dsn
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        if not self.pool:
            try:
                self.pool = await asyncpg.create_pool(dsn=self.dsn, min_size=1, max_size=10)
                # Test connection by executing a simple query
                async with self.pool.acquire() as connection:
                    await connection.fetchval('SELECT 1')
                print(f"Successfully connected to PostgreSQL.")
            except Exception as e: 
                print(f"PostgreSQL connection failed: {e}")
                self.pool = None
                raise 

    async def disconnect(self) -> None:
        if self.pool:
            await self.pool.close()
            self.pool = None
            print("Disconnected from PostgreSQL.")

    def _prep_data_for_insert(self, data: Dict[str, Any]) -> tuple:
        columns = ', '.join(data.keys())
        placeholders = ', '.join([f'${i+1}' for i in range(len(data))])
        values = list(data.values())
        return columns, placeholders, values

    def _prep_data_for_update(self, data: Dict[str, Any], start_index: int = 1) -> tuple:
        set_clause = ', '.join([f"{key} = ${i+start_index}" for i, key in enumerate(data.keys())])
        values = list(data.values())
        return set_clause, values
    
    def _prep_query_conditions(self, query: Dict[str, Any], start_index: int = 1) -> tuple:
        conditions = []
        values = []
        for i, (key, value) in enumerate(query.items()):
            conditions.append(f"{key} = ${i+start_index}")
            values.append(value)
        where_clause = " AND ".join(conditions) if conditions else "1=1" # Handle empty query
        return where_clause, values

    async def insert(self, table_name: str, data: Dict[str, Any]) -> Any: 
        if not self.pool:
            raise ConnectionError("Database not connected. Call connect() first.")
        
        # The DatabasePort defines collection, but for SQL it's table_name
        columns, placeholders, values = self._prep_data_for_insert(data)
        # Assuming 'id' is the primary key and is returned. Adjust if PK name is different.
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders}) RETURNING id"
        
        try:
            async with self.pool.acquire() as connection:
                return await connection.fetchval(sql, *values)
        except asyncpg.PostgresError as e:
            print(f"PostgreSQL insert operation failed: {e}")
            raise

    async def find_one(self, table_name: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.pool:
            raise ConnectionError("Database not connected. Call connect() first.")

        where_clause, values = self._prep_query_conditions(query)
        sql = f"SELECT * FROM {table_name} WHERE {where_clause} LIMIT 1"
        
        try:
            async with self.pool.acquire() as connection:
                row = await connection.fetchrow(sql, *values)
                return dict(row) if row else None
        except asyncpg.PostgresError as e:
            print(f"PostgreSQL find_one operation failed: {e}")
            raise

    async def find_many(self, table_name: str, query: Dict[str, Any], limit: int = 0) -> List[Dict[str, Any]]:
        if not self.pool:
            raise ConnectionError("Database not connected. Call connect() first.")

        where_clause, values = self._prep_query_conditions(query)
        sql = f"SELECT * FROM {table_name} WHERE {where_clause}"
        
        final_values = list(values) # Create a mutable copy for potentially adding limit
        if limit > 0:
            sql += f" LIMIT ${len(final_values) + 1}"
            final_values.append(limit)
        
        try:
            async with self.pool.acquire() as connection:
                rows = await connection.fetch(sql, *final_values)
                return [dict(row) for row in rows]
        except asyncpg.PostgresError as e:
            print(f"PostgreSQL find_many operation failed: {e}")
            raise

    async def update_one(self, table_name: str, query: Dict[str, Any], data: Dict[str, Any]) -> bool:
        if not self.pool:
            raise ConnectionError("Database not connected. Call connect() first.")

        set_clause, set_values = self._prep_data_for_update(data)
        where_clause, where_values = self._prep_query_conditions(query, start_index=len(set_values) + 1)
        
        # To truly update only one, you might need a subquery with LIMIT if not using a unique key in WHERE
        # Example: UPDATE {table_name} SET ... WHERE ctid = (SELECT ctid FROM {table_name} WHERE {where_clause} LIMIT 1)
        # This simplified version updates all matching rows and returns if any were affected.
        # For the DatabasePort's update_one, we expect it to target one specific document ideally via a unique key.
        # If the query is not specific, it could update more. The return bool indicates if *at least one* was modified.
        # A stricter version would add "AND ctid = (SELECT ctid FROM {table_name} WHERE {where_clause} LIMIT 1)" to SQL.
        # For now, we stick to the simpler interpretation.
        sql = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
        
        try:
            async with self.pool.acquire() as connection:
                status = await connection.execute(sql, *set_values, *where_values)
                affected_rows_str = status.split(' ')[-1]
                affected_rows = int(affected_rows_str) if affected_rows_str.isdigit() else 0
                return affected_rows > 0
        except asyncpg.PostgresError as e:
            print(f"PostgreSQL update_one operation failed: {e}")
            raise

    async def update_many(self, table_name: str, query: Dict[str, Any], data: Dict[str, Any]) -> int:
        if not self.pool:
            raise ConnectionError("Database not connected. Call connect() first.")

        set_clause, set_values = self._prep_data_for_update(data)
        where_clause, where_values = self._prep_query_conditions(query, start_index=len(set_values) + 1)
        sql = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
        
        try:
            async with self.pool.acquire() as connection:
                status = await connection.execute(sql, *set_values, *where_values)
                affected_rows_str = status.split(' ')[-1]
                affected_rows = int(affected_rows_str) if affected_rows_str.isdigit() else 0
                return affected_rows
        except asyncpg.PostgresError as e:
            print(f"PostgreSQL update_many operation failed: {e}")
            raise

    async def delete_one(self, table_name: str, query: Dict[str, Any]) -> bool:
        if not self.pool:
            raise ConnectionError("Database not connected. Call connect() first.")
        
        where_clause, values = self._prep_query_conditions(query)
        # Similar to update_one, this deletes based on query. To strictly delete one, a subquery with LIMIT is needed.
        # e.g., DELETE FROM {table_name} WHERE ctid = (SELECT ctid FROM {table_name} WHERE {where_clause} LIMIT 1)
        # This simpler version deletes all matching the query and returns True if any were deleted.
        sql = f"DELETE FROM {table_name} WHERE {where_clause}"
        
        try:
            async with self.pool.acquire() as connection:
                status = await connection.execute(sql, *values)
                affected_rows_str = status.split(' ')[-1]
                affected_rows = int(affected_rows_str) if affected_rows_str.isdigit() else 0
                return affected_rows > 0 
        except asyncpg.PostgresError as e:
            print(f"PostgreSQL delete_one operation failed: {e}")
            raise

    async def delete_many(self, table_name: str, query: Dict[str, Any]) -> int:
        if not self.pool:
            raise ConnectionError("Database not connected. Call connect() first.")

        where_clause, values = self._prep_query_conditions(query)
        sql = f"DELETE FROM {table_name} WHERE {where_clause}"
        
        try:
            async with self.pool.acquire() as connection:
                status = await connection.execute(sql, *values)
                affected_rows_str = status.split(' ')[-1]
                affected_rows = int(affected_rows_str) if affected_rows_str.isdigit() else 0
                return affected_rows
        except asyncpg.PostgresError as e:
            print(f"PostgreSQL delete_many operation failed: {e}")
            raise
