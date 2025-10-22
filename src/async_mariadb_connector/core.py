# Core async connector
import asyncio
import aiomysql
import logging
from typing import Optional, Any, List, Dict, AsyncGenerator
from tenacity import retry, stop_after_attempt, wait_exponential
import pandas as pd

from .exceptions import ConnectionError, QueryError
from .config import load_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AsyncMariaDB:
    """
    An asynchronous wrapper for aiomysql with connection pooling,
    DataFrame integration, and retry logic.
    """
    _pool: Optional[aiomysql.Pool] = None

    def __init__(self, **kwargs):
        """
        Initializes the connector.
        Configuration can be passed as keyword arguments (e.g., host, user, password)
        or will be loaded from a .env file.
        """
        self.db_config = load_config(**kwargs)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def _get_pool(self) -> aiomysql.Pool:
        """
        Initializes and returns the connection pool.
        Retries on failure.
        """
        if self._pool is None:
            try:
                logger.info("Creating database connection pool.")
                self._pool = await aiomysql.create_pool(
                    host=self.db_config['host'],
                    port=self.db_config['port'],
                    user=self.db_config['user'],
                    password=self.db_config['password'],
                    db=self.db_config['db'],
                    minsize=self.db_config['minsize'],
                    maxsize=self.db_config['maxsize'],
                    autocommit=self.db_config['autocommit'],
                    loop=asyncio.get_event_loop()
                )
            except Exception as e:
                logger.error(f"Failed to create connection pool: {e}")
                raise ConnectionError("Could not establish a connection pool.") from e
        return self._pool

    async def get_connection(self) -> aiomysql.Connection:
        """Acquires a connection from the pool."""
        pool = await self._get_pool()
        try:
            return await pool.acquire()
        except Exception as e:
            logger.error(f"Failed to acquire connection from pool: {e}")
            raise ConnectionError(f"Failed to acquire connection from pool: {e}") from e

    async def release_connection(self, connection: aiomysql.Connection):
        """Releases a connection back to the pool."""
        if self._pool:
            self._pool.release(connection)

    async def execute(self, query: str, params: Optional[tuple] = None, commit: bool = True) -> int:
        """
        Execute a query (INSERT, UPDATE, DELETE) and return the number of affected rows.
        """
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(query, params)
                    if commit and not self.db_config['autocommit']:
                        await conn.commit()
                    return cur.rowcount
        except Exception as e:
            logger.error(f"Query failed: {query} | Error: {e}")
            raise QueryError("Query execution failed.") from e

    async def executemany(self, query: str, params_list: List[tuple], commit: bool = True) -> int:
        """
        Execute a query with multiple parameter sets (bulk operation).
        
        This is ideal for batch inserts, updates, or deletes where you have
        the same query structure but multiple sets of parameters.
        
        Args:
            query: SQL query with placeholders (e.g., "INSERT INTO users (name, age) VALUES (%s, %s)")
            params_list: List of parameter tuples, one for each execution
            commit: Whether to commit the transaction (default: True)
        
        Returns:
            Total number of affected rows
        
        Example:
            >>> data = [("Alice", 25), ("Bob", 30), ("Charlie", 35)]
            >>> rows = await db.executemany(
            ...     "INSERT INTO users (name, age) VALUES (%s, %s)",
            ...     data
            ... )
            >>> print(f"Inserted {rows} rows")
        
        Note:
            This is much more efficient than calling execute() in a loop,
            as it sends all data in a single batch to the database.
        """
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.executemany(query, params_list)
                    if commit and not self.db_config['autocommit']:
                        await conn.commit()
                    return cur.rowcount
        except Exception as e:
            logger.error(f"Batch query failed: {query} | Error: {e}")
            raise QueryError("Batch query execution failed.") from e

    async def fetch(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Fetch all rows from a SELECT query.
        """
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute(query, params)
                    result = await cur.fetchall()
                    return result
        except Exception as e:
            logger.error(f"Fetch query failed: {query} | Error: {e}")
            raise QueryError("Fetch query failed.") from e

    async def fetch_all(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Fetch all rows from a query."""
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute(query, params)
                    result = await cur.fetchall()
                    return list(result) if result else []
        except Exception as e:
            logger.error(f"Fetch all failed: {query} | Error: {e}")
            raise QueryError("Fetch all operation failed.") from e

    async def fetch_one(self, query: str, params: Optional[tuple] = None) -> Optional[Dict[str, Any]]:
        """Fetch one row from a query."""
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute(query, params)
                    return await cur.fetchone()
        except Exception as e:
            logger.error(f"Fetch one failed: {query} | Error: {e}")
            raise QueryError("Fetch one operation failed.") from e

    async def fetch_stream(self, query: str, params: tuple = None) -> AsyncGenerator[dict, None]:
        """
        Fetch rows one by one using an async generator (server-side cursor).
        """
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute(query, params)
                    async for row in cur:
                        yield row
        except Exception as e:
            logger.error(f"Streaming query failed: {e}")
            raise QueryError(f"Streaming query failed: {e}") from e

    async def fetch_all_df(self, query: str, params: tuple = None) -> pd.DataFrame:
        """
        Executes a query and returns the results as a pandas DataFrame.
        """
        logger.info(f"Fetching all rows into DataFrame for query: {query}")
        try:
            results = await self.fetch_all(query, params)
            return pd.DataFrame(results)
        except Exception as e:
            logger.error(f"Failed to fetch data into DataFrame: {e}")
            raise QueryError(f"Failed to fetch data into DataFrame: {e}") from e

    def get_pool_stats(self) -> Dict[str, int]:
        """
        Get connection pool statistics for monitoring and debugging.
        
        Returns:
            Dictionary with pool metrics:
            - 'size': Current number of connections in the pool
            - 'max_size': Maximum allowed connections
            - 'min_size': Minimum maintained connections
            - 'in_use': Number of connections currently in use
            - 'available': Number of free connections available
        
        Example:
            >>> stats = db.get_pool_stats()
            >>> print(f"Pool: {stats['in_use']}/{stats['size']} in use")
            >>> if stats['available'] == 0:
            ...     logger.warning("Connection pool exhausted!")
        
        Note:
            Useful for production monitoring, alerting, and capacity planning.
            Integrate with Prometheus, Grafana, or CloudWatch for observability.
        """
        if self._pool is None:
            raise ConnectionError("Connection pool not initialized. Call connect() first or use async context manager.")
        
        return {
            'size': self._pool.size,
            'max_size': self._pool.maxsize,
            'min_size': self._pool.minsize,
            'in_use': self._pool.size - self._pool.freesize,
            'available': self._pool.freesize
        }

    async def close(self):
        """
        Gracefully close the connection pool.
        """
        if self._pool:
            self._pool.close()
            await self._pool.wait_closed()
            logger.info("Database connection pool closed.")
            self._pool = None

    async def __aenter__(self):
        await self._get_pool()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
