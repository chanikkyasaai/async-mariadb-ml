import pytest
import pytest_asyncio
import pandas as pd
from async_mariadb_connector import AsyncMariaDB

@pytest_asyncio.fixture
async def db():
    """Provides a database connection fixture for tests."""
    db_conn = AsyncMariaDB()
    try:
        # Ensure a clean slate for each test
        await db_conn.execute("DROP TABLE IF EXISTS dataframe_test_table")
        yield db_conn
    finally:
        await db_conn.close()

@pytest.mark.asyncio
async def test_query_to_dataframe(db: AsyncMariaDB):
    """
    Tests the query_to_dataframe function to ensure it returns a valid DataFrame.
    """
    table_name = "dataframe_test_table"
    await db.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INT,
            name VARCHAR(50)
        )
    """)
    
    # Insert test data
    await db.execute(f"INSERT INTO {table_name} (id, name) VALUES (%s, %s)", (1, "Alice"))
    await db.execute(f"INSERT INTO {table_name} (id, name) VALUES (%s, %s)", (2, "Bob"))

    # Call the function to be tested
    df = await db.fetch_all_df(f"SELECT * FROM {table_name}")

    # Assertions
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert list(df.columns) == ["id", "name"]
    assert df["name"].iloc[0] == "Alice"

    # Test with an empty result
    df_empty = await db.fetch_all_df(f"SELECT * FROM {table_name} WHERE id > 100")
    assert isinstance(df_empty, pd.DataFrame)
    assert df_empty.empty

    # Clean up
    await db.execute(f"DROP TABLE {table_name}")
