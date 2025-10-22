# pytest-asyncio based tests
import pytest
import pytest_asyncio
from async_mariadb_connector import AsyncMariaDB, ConnectionError, QueryError

@pytest_asyncio.fixture
async def db():
    async with AsyncMariaDB() as db_conn:
        yield db_conn

@pytest.mark.asyncio
async def test_connection(db: AsyncMariaDB):
    assert db._pool is not None
    # Try a simple query to ensure the connection is live
    result = await db.fetch("SELECT 1")
    assert result[0]['1'] == 1

@pytest.mark.asyncio
async def test_execute_and_fetch(db: AsyncMariaDB):
    await db.execute("CREATE TABLE IF NOT EXISTS test_table (id INT, name VARCHAR(50))")
    
    try:
        await db.execute("INSERT INTO test_table (id, name) VALUES (1, 'test')")
        
        result = await db.fetch("SELECT * FROM test_table WHERE id = 1")
        assert len(result) == 1
        assert result[0]['name'] == 'test'
    
    finally:
        await db.execute("DROP TABLE test_table")

@pytest.mark.asyncio
async def test_failed_query(db: AsyncMariaDB):
    with pytest.raises(QueryError):
        await db.fetch("SELECT * FROM non_existent_table")

@pytest.mark.asyncio
async def test_streaming_fetch(db: AsyncMariaDB):
    await db.execute("CREATE TABLE IF NOT EXISTS stream_test (id INT)")
    try:
        for i in range(10):
            await db.execute("INSERT INTO stream_test (id) VALUES (%s)", (i,), commit=False)
        await db.execute("COMMIT")

        results = []
        async for row in db.fetch_stream("SELECT * FROM stream_test ORDER BY id"):
            results.append(row['id'])
        
        assert results == list(range(10))
    finally:
        await db.execute("DROP TABLE stream_test")

@pytest.mark.asyncio
async def test_connection_error():
    """Test that providing invalid credentials raises a ConnectionError."""
    db_invalid = AsyncMariaDB(user="invalid_user", password="invalid_password")
    with pytest.raises(ConnectionError):
        # The error is raised when a connection is actually acquired from the pool
        await db_invalid.get_connection()
    await db_invalid.close()


@pytest.mark.asyncio
async def test_query_error(db: AsyncMariaDB):
    """Test that a query with a syntax error raises a QueryError."""
    with pytest.raises(QueryError):
        await db.fetch("SELECT * FORM test_table")  # Intentional syntax error


@pytest.mark.asyncio
async def test_executemany(db: AsyncMariaDB):
    """Test batch insert using executemany."""
    await db.execute("CREATE TABLE IF NOT EXISTS batch_test (id INT, name VARCHAR(50), age INT)")
    
    try:
        # Prepare batch data
        data = [
            (1, "Alice", 25),
            (2, "Bob", 30),
            (3, "Charlie", 35),
            (4, "David", 40),
            (5, "Eve", 45)
        ]
        
        # Execute batch insert
        rows_affected = await db.executemany(
            "INSERT INTO batch_test (id, name, age) VALUES (%s, %s, %s)",
            data
        )
        
        # Verify row count
        assert rows_affected == 5
        
        # Verify data was inserted correctly
        results = await db.fetch_all("SELECT * FROM batch_test ORDER BY id")
        assert len(results) == 5
        assert results[0]['name'] == "Alice"
        assert results[0]['age'] == 25
        assert results[4]['name'] == "Eve"
        assert results[4]['age'] == 45
        
    finally:
        await db.execute("DROP TABLE batch_test")

@pytest.mark.asyncio
async def test_get_pool_stats(db: AsyncMariaDB):
    """Test connection pool statistics monitoring."""
    # Get pool stats
    stats = db.get_pool_stats()
    
    # Verify all required keys are present
    assert 'size' in stats
    assert 'max_size' in stats
    assert 'min_size' in stats
    assert 'in_use' in stats
    assert 'available' in stats
    
    # Verify types are integers
    assert isinstance(stats['size'], int)
    assert isinstance(stats['max_size'], int)
    assert isinstance(stats['min_size'], int)
    assert isinstance(stats['in_use'], int)
    assert isinstance(stats['available'], int)
    
    # Verify logical constraints
    assert stats['size'] >= 0
    assert stats['max_size'] > 0
    assert stats['min_size'] >= 0
    assert stats['in_use'] >= 0
    assert stats['available'] >= 0
    assert stats['size'] == stats['in_use'] + stats['available']
    assert stats['size'] <= stats['max_size']
    assert stats['min_size'] <= stats['max_size']
    
    # Test that pool is functional (at least one connection available)
    assert stats['size'] > 0, "Pool should have at least one connection"
