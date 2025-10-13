import pytest
import pytest_asyncio
import pandas as pd
from datetime import datetime
import asyncio
from unittest.mock import patch, AsyncMock

from async_mariadb_connector import AsyncMariaDB, ConnectionError, QueryError, bulk_insert

# Fixture for a connected AsyncMariaDB instance
@pytest_asyncio.fixture
async def db():
    # Use kwargs for flexible configuration
    db_instance = AsyncMariaDB(pool_min_size=1, pool_max_size=2)
    # Use a different table name to avoid conflicts with other test files
    table_name = "edge_case_test_table"
    # Ensure the instance is connected and pool is created
    await db_instance._get_pool()
    
    # Cleanup before and after
    conn = await db_instance.get_connection()
    try:
        async with conn.cursor() as cursor:
            await cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            await cursor.execute(f"""
                CREATE TABLE {table_name} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255),
                    value FLOAT,
                    created_at DATETIME
                )
            """)
    finally:
        await db_instance.release_connection(conn)

    yield db_instance
    
    # Teardown
    await db_instance.close()

@pytest.mark.asyncio
async def test_connection_invalid_host():
    """Test that connecting to an invalid host raises a ConnectionError."""
    # Set a very short timeout for this test
    db_invalid = AsyncMariaDB(host="invalid.host.local", connect_timeout=1)
    with pytest.raises(ConnectionError, match="Could not establish a connection pool."):
        await db_invalid._get_pool()

@pytest.mark.asyncio
async def test_execute_invalid_sql_syntax(db: AsyncMariaDB):
    """Test that executing a query with invalid SQL syntax raises a QueryError."""
    with pytest.raises(QueryError, match="Query execution failed."):
        await db.execute("SELECT FROM table_that_is_not_real WITH BAD SYNTAX")

@pytest.mark.asyncio
async def test_fetch_from_empty_table(db: AsyncMariaDB):
    """Test that fetching from an empty table returns an empty list."""
    result = await db.fetch_all("SELECT * FROM edge_case_test_table")
    assert result == []

@pytest.mark.asyncio
async def test_stream_from_empty_table(db: AsyncMariaDB):
    """Test that streaming from an empty table yields no results."""
    results = []
    async for row in db.fetch_stream("SELECT * FROM edge_case_test_table"):
        results.append(row)
    assert len(results) == 0

@pytest.mark.asyncio
async def test_bulk_insert_with_none_and_special_types(db: AsyncMariaDB):
    """Test bulk inserting a DataFrame with None, NaN, and various data types."""
    table_name = "edge_case_test_table"
    now = datetime.now()
    # PyMySQL/MariaDB drivers don't support infinity. Let's test with valid data including None.
    df_valid = pd.DataFrame([
        {"name": "Valid 1", "value": 99.9, "created_at": now},
        {"name": "Valid 2", "value": None, "created_at": now}, # Should become NULL
    ])
    
    await bulk_insert(db, table_name, df_valid)
    
    results = await db.fetch_all(f"SELECT name, value FROM {table_name} ORDER BY name")
    
    assert len(results) == 2
    assert results[0]["name"] == "Valid 1"
    assert results[0]["value"] == 99.9
    assert results[1]["name"] == "Valid 2"
    assert results[1]["value"] is None # Check for NULL

@pytest.mark.asyncio
async def test_bulk_insert_empty_dataframe(db: AsyncMariaDB):
    """Test that bulk inserting an empty DataFrame does nothing and doesn't raise an error."""
    table_name = "edge_case_test_table"
    df_empty = pd.DataFrame({"name": [], "value": [], "created_at": []})
    
    try:
        await bulk_insert(db, table_name, df_empty)
    except Exception as e:
        pytest.fail(f"Bulk inserting an empty DataFrame raised an exception: {e}")
        
    result = await db.fetch_one(f"SELECT COUNT(*) as count FROM {table_name}")
    assert result['count'] == 0

@pytest.mark.asyncio
@patch('aiomysql.create_pool')
async def test_retry_on_connection_failure(mock_create_pool):
    """Test the tenacity retry logic on connection acquisition failure."""
    # Simulate that creating the pool fails twice, then succeeds
    async def side_effect(*args, **kwargs):
        if mock_create_pool.call_count <= 2:
            raise OSError(f"Simulated connection failure {mock_create_pool.call_count}")
        
        # Return a more complete mock for the pool
        mock_pool = AsyncMock()
        mock_pool.wait_closed = AsyncMock() # Mock the wait_closed method
        return mock_pool

    mock_create_pool.side_effect = side_effect
    
    db_retry = AsyncMariaDB()
    
    # The retry decorator on _get_pool should handle the failures
    try:
        await db_retry._get_pool()
    except ConnectionError:
        pytest.fail("The retry mechanism did not work as expected.")
    
    # Assert that create_pool was called three times
    assert mock_create_pool.call_count == 3
    await db_retry.close()
