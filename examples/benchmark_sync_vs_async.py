# Benchmarking script to compare synchronous vs. asynchronous performance
import asyncio
import time
import pandas as pd
import pymysql
from faker import Faker
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Local application imports
from async_mariadb_connector import AsyncMariaDB, bulk_insert

# --- Configuration ---
NUM_RECORDS = 10000
CONCURRENT_TASKS = 100
TABLE_NAME_ASYNC = "benchmark_async"
TABLE_NAME_SYNC = "benchmark_sync"

# --- Synchronous Operations using pymysql ---
def get_sync_connection():
    """Establishes a synchronous database connection."""
    return pymysql.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", 3307)),
        user=os.getenv("DB_USER", "your_user"),
        password=os.getenv("DB_PASSWORD", "your_password"),
        database=os.getenv("DB_NAME", "your_db"),
        autocommit=True
    )

def sync_bulk_insert(records):
    """Inserts records synchronously."""
    conn = get_sync_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {TABLE_NAME_SYNC}")
            cursor.execute(f"""
                CREATE TABLE {TABLE_NAME_SYNC} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255),
                    email VARCHAR(255)
                )
            """)
            sql = f"INSERT INTO {TABLE_NAME_SYNC} (name, email) VALUES (%s, %s)"
            # executemany with tuples
            data = [tuple(row) for row in records]
            cursor.executemany(sql, data)
    finally:
        conn.close()

def sync_concurrent_reads():
    """Simulates concurrent reads synchronously (sequentially)."""
    conn = get_sync_connection()
    try:
        with conn.cursor() as cursor:
            for _ in range(CONCURRENT_TASKS):
                cursor.execute(f"SELECT * FROM {TABLE_NAME_SYNC} LIMIT 100")
                _ = cursor.fetchall()
    finally:
        conn.close()

# --- Asynchronous Operations using our library ---
async def async_bulk_insert(db, records):
    """Inserts records asynchronously."""
    await db.execute(f"DROP TABLE IF EXISTS {TABLE_NAME_ASYNC}")
    await db.execute(f"""
        CREATE TABLE {TABLE_NAME_ASYNC} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            email VARCHAR(255)
        )
    """)
    df = pd.DataFrame(records, columns=["name", "email"])
    await bulk_insert(db, TABLE_NAME_ASYNC, df)

async def async_concurrent_reads(db):
    """Simulates concurrent reads asynchronously."""
    tasks = [
        db.fetch_all(f"SELECT * FROM {TABLE_NAME_ASYNC} LIMIT 100")
        for _ in range(CONCURRENT_TASKS)
    ]
    await asyncio.gather(*tasks)

async def main():
    """Main function to run and compare benchmarks."""
    fake = Faker()
    records_to_insert = [(fake.name(), fake.email()) for _ in range(NUM_RECORDS)]

    # --- Benchmark Sync Bulk Insert ---
    print(f"Running synchronous bulk insert for {NUM_RECORDS} records...")
    start_time = time.perf_counter()
    sync_bulk_insert(records_to_insert)
    sync_insert_time = time.perf_counter() - start_time
    print(f"Sync insert time: {sync_insert_time:.4f} seconds")

    # --- Benchmark Async Bulk Insert ---
    db = AsyncMariaDB()
    try:
        print(f"\nRunning asynchronous bulk insert for {NUM_RECORDS} records...")
        start_time = time.perf_counter()
        await async_bulk_insert(db, records_to_insert)
        async_insert_time = time.perf_counter() - start_time
        print(f"Async insert time: {async_insert_time:.4f} seconds")

        # --- Benchmark Sync Concurrent Reads ---
        print(f"\nRunning synchronous concurrent reads ({CONCURRENT_TASKS} tasks)...")
        start_time = time.perf_counter()
        sync_concurrent_reads()
        sync_read_time = time.perf_counter() - start_time
        print(f"Sync read time: {sync_read_time:.4f} seconds")

        # --- Benchmark Async Concurrent Reads ---
        print(f"\nRunning asynchronous concurrent reads ({CONCURRENT_TASKS} tasks)...")
        start_time = time.perf_counter()
        await async_concurrent_reads(db)
        async_read_time = time.perf_counter() - start_time
        print(f"Async read time: {async_read_time:.4f} seconds")

    finally:
        await db.close()

    # --- Print Results Table ---
    print("\n--- Benchmark Results ---")
    results = {
        "Operation": ["Bulk Insert", "Concurrent Reads"],
        "Sync Time (s)": [f"{sync_insert_time:.4f}", f"{sync_read_time:.4f}"],
        "Async Time (s)": [f"{async_insert_time:.4f}", f"{async_read_time:.4f}"],
    }
    results_df = pd.DataFrame(results)
    print(results_df.to_markdown(index=False))
    print("\nLower is better.")

if __name__ == "__main__":
    # Ensure the package is installed, or add src to path for local dev
    import sys
    import os
    # Add the project root to the Python path to allow imports from `src`
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    asyncio.run(main())
