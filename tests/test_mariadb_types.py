"""
Tests for MariaDB-specific data types and features.
Validates JSON, DECIMAL, NULL/NaN handling, datetime/timezone, and utf8mb4 charset.
"""
import pytest
import pytest_asyncio
import pandas as pd
import numpy as np
import json
from decimal import Decimal
from datetime import datetime, timezone
from async_mariadb_connector import AsyncMariaDB, bulk_insert

@pytest_asyncio.fixture
async def db():
    """Fixture providing a database connection."""
    async with AsyncMariaDB() as db_conn:
        yield db_conn


@pytest.mark.asyncio
async def test_json_type(db: AsyncMariaDB):
    """Test JSON column storage and retrieval."""
    # Create table with JSON column
    await db.execute("""
        CREATE TABLE IF NOT EXISTS test_json (
            id INT AUTO_INCREMENT PRIMARY KEY,
            data JSON
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    
    try:
        # Insert JSON data
        test_data = {"name": "Alice", "age": 30, "verified": True, "tags": ["python", "async"]}
        await db.execute(
            "INSERT INTO test_json (data) VALUES (%s)",
            (json.dumps(test_data),)
        )
        
        # Fetch and verify
        result = await db.fetch_one("SELECT data FROM test_json WHERE id = 1")
        retrieved_data = json.loads(result['data'])
        
        assert retrieved_data == test_data
        assert retrieved_data['name'] == "Alice"
        assert retrieved_data['verified'] is True
        assert len(retrieved_data['tags']) == 2
        
    finally:
        await db.execute("DROP TABLE IF EXISTS test_json")


@pytest.mark.asyncio
async def test_decimal_precision(db: AsyncMariaDB):
    """Test DECIMAL type for exact precision (financial calculations)."""
    await db.execute("""
        CREATE TABLE IF NOT EXISTS test_decimal (
            id INT AUTO_INCREMENT PRIMARY KEY,
            amount DECIMAL(10, 2)
        ) ENGINE=InnoDB
    """)
    
    try:
        # Insert DECIMAL values
        test_amounts = [Decimal("1234.56"), Decimal("9999.99"), Decimal("0.01")]
        for amount in test_amounts:
            await db.execute("INSERT INTO test_decimal (amount) VALUES (%s)", (amount,))
        
        # Fetch as DataFrame
        df = await db.fetch_all_df("SELECT amount FROM test_decimal ORDER BY id")
        
        assert len(df) == 3
        # Check that DECIMAL precision is maintained
        assert float(df.iloc[0]['amount']) == 1234.56
        assert float(df.iloc[1]['amount']) == 9999.99
        assert float(df.iloc[2]['amount']) == 0.01
        
    finally:
        await db.execute("DROP TABLE IF EXISTS test_decimal")


@pytest.mark.asyncio
async def test_null_and_nan_handling(db: AsyncMariaDB):
    """Test NULL and NaN handling in bulk operations."""
    await db.execute("""
        CREATE TABLE IF NOT EXISTS test_null (
            id INT AUTO_INCREMENT PRIMARY KEY,
            value FLOAT,
            name VARCHAR(255)
        ) ENGINE=InnoDB
    """)
    
    try:
        # Create DataFrame with NaN and None
        df = pd.DataFrame({
            'value': [1.5, np.nan, 3.7, np.nan],
            'name': ['Alice', None, 'Charlie', 'David']
        })
        
        # Bulk insert
        await bulk_insert(db, "test_null", df)
        
        # Fetch and verify
        results = await db.fetch_all("SELECT id, value, name FROM test_null ORDER BY id")
        
        assert len(results) == 4
        assert results[0]['value'] == 1.5
        assert results[0]['name'] == 'Alice'
        assert results[1]['value'] is None  # NaN → NULL
        assert results[1]['name'] is None
        assert results[2]['value'] == 3.7
        assert results[2]['name'] == 'Charlie'
        
    finally:
        await db.execute("DROP TABLE IF EXISTS test_null")


@pytest.mark.asyncio
async def test_datetime_and_timezone(db: AsyncMariaDB):
    """Test TIMESTAMP and datetime handling."""
    await db.execute("""
        CREATE TABLE IF NOT EXISTS test_datetime (
            id INT AUTO_INCREMENT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            event_time DATETIME
        ) ENGINE=InnoDB
    """)
    
    try:
        # Insert with explicit datetime
        test_time = datetime(2025, 10, 21, 12, 30, 45)
        await db.execute(
            "INSERT INTO test_datetime (event_time) VALUES (%s)",
            (test_time,)
        )
        
        # Fetch and verify
        result = await db.fetch_one("SELECT created_at, event_time FROM test_datetime WHERE id = 1")
        
        assert result['event_time'] == test_time
        assert isinstance(result['created_at'], datetime)
        
        # Verify created_at is recent (within last minute)
        now = datetime.now()
        time_diff = (now - result['created_at']).total_seconds()
        assert 0 <= time_diff < 60, "Timestamp should be recent"
        
    finally:
        await db.execute("DROP TABLE IF EXISTS test_datetime")


@pytest.mark.asyncio
async def test_utf8mb4_charset(db: AsyncMariaDB):
    """Test utf8mb4 support for emojis and 4-byte characters."""
    await db.execute("""
        CREATE TABLE IF NOT EXISTS test_utf8mb4 (
            id INT AUTO_INCREMENT PRIMARY KEY,
            text VARCHAR(255)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    
    try:
        # Insert text with emojis and special characters
        test_strings = [
            "Hello 👋 World 🌍",
            "Python 🐍 + MariaDB 🚀",
            "日本語テキスト",  # Japanese
            "Emoji: 😀😃😄😁"
        ]
        
        for text in test_strings:
            await db.execute("INSERT INTO test_utf8mb4 (text) VALUES (%s)", (text,))
        
        # Fetch and verify
        df = await db.fetch_all_df("SELECT text FROM test_utf8mb4 ORDER BY id")
        
        assert len(df) == 4
        for i, expected in enumerate(test_strings):
            assert df.iloc[i]['text'] == expected
        
    finally:
        await db.execute("DROP TABLE IF EXISTS test_utf8mb4")


@pytest.mark.asyncio
async def test_json_in_dataframe(db: AsyncMariaDB):
    """Test bulk insert of DataFrame with JSON-serializable data."""
    await db.execute("""
        CREATE TABLE IF NOT EXISTS test_json_df (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            metadata JSON
        ) ENGINE=InnoDB
    """)
    
    try:
        # Create DataFrame with dict objects
        df = pd.DataFrame({
            'user_id': [1, 2, 3],
            'metadata': [
                json.dumps({"role": "admin", "verified": True}),
                json.dumps({"role": "user", "verified": False}),
                json.dumps({"role": "guest", "verified": None})
            ]
        })
        
        # Bulk insert
        await bulk_insert(db, "test_json_df", df)
        
        # Fetch and verify
        results = await db.fetch_all("SELECT user_id, metadata FROM test_json_df ORDER BY user_id")
        
        assert len(results) == 3
        
        meta1 = json.loads(results[0]['metadata'])
        assert meta1['role'] == 'admin'
        assert meta1['verified'] is True
        
        meta2 = json.loads(results[1]['metadata'])
        assert meta2['role'] == 'user'
        assert meta2['verified'] is False
        
    finally:
        await db.execute("DROP TABLE IF EXISTS test_json_df")


@pytest.mark.asyncio
async def test_large_text_fields(db: AsyncMariaDB):
    """Test TEXT and LONGTEXT column types."""
    await db.execute("""
        CREATE TABLE IF NOT EXISTS test_text (
            id INT AUTO_INCREMENT PRIMARY KEY,
            content TEXT,
            large_content LONGTEXT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    
    try:
        # Insert large text (10KB)
        large_text = "A" * 10000
        await db.execute(
            "INSERT INTO test_text (content, large_content) VALUES (%s, %s)",
            ("Short text", large_text)
        )
        
        # Fetch and verify
        result = await db.fetch_one("SELECT content, large_content FROM test_text WHERE id = 1")
        
        assert result['content'] == "Short text"
        assert len(result['large_content']) == 10000
        assert result['large_content'] == large_text
        
    finally:
        await db.execute("DROP TABLE IF EXISTS test_text")
