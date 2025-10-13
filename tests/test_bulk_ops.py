# Bulk insert stress tests
import pytest
import pytest_asyncio
import pandas as pd
import numpy as np
from async_mariadb_connector import AsyncMariaDB, bulk_insert, BulkOperationError

@pytest_asyncio.fixture
async def db():
    async with AsyncMariaDB() as db_conn:
        await db_conn.execute("""
            CREATE TABLE IF NOT EXISTS test_bulk (
                id INT AUTO_INCREMENT PRIMARY KEY,
                value_float FLOAT,
                value_str VARCHAR(100)
            )
        """)
        yield db_conn
        await db_conn.execute("DROP TABLE test_bulk")

@pytest.mark.asyncio
async def test_bulk_insert_success(db: AsyncMariaDB):
    num_rows = 500
    data = {
        'value_float': np.random.rand(num_rows),
        'value_str': [f'string_{i}' for i in range(num_rows)]
    }
    df = pd.DataFrame(data)

    await bulk_insert(db, 'test_bulk', df)

    result = await db.fetch("SELECT COUNT(*) as count FROM test_bulk")
    assert result[0]['count'] == num_rows

@pytest.mark.asyncio
async def test_bulk_insert_empty_dataframe(db: AsyncMariaDB):
    df = pd.DataFrame()
    await bulk_insert(db, 'test_bulk', df)
    result = await db.fetch("SELECT COUNT(*) as count FROM test_bulk")
    assert result[0]['count'] == 0

@pytest.mark.asyncio
async def test_bulk_insert_wrong_table(db: AsyncMariaDB):
    df = pd.DataFrame({'col1': [1, 2]})
    with pytest.raises(BulkOperationError):
        await bulk_insert(db, 'non_existent_table', df)
