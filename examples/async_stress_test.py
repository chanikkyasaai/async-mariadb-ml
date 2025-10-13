import asyncio
import time
import pandas as pd
from faker import Faker
from async_mariadb_connector import AsyncMariaDB, bulk_insert

# --- Configuration ---
NUM_RECORDS = 1000
CONCURRENT_TASKS = 100  # Number of concurrent insert tasks
RECORDS_PER_TASK = NUM_RECORDS // CONCURRENT_TASKS

TABLE_NAME = "stress_test_table"

async def setup_table(db: AsyncMariaDB):
    """Create the table for the stress test."""
    await db.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")
    await db.execute(f"""
        CREATE TABLE {TABLE_NAME} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            email VARCHAR(255),
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print(f"Table '{TABLE_NAME}' created.")

async def run_insert_task(db: AsyncMariaDB, records: pd.DataFrame):
    """A single task to bulk insert a chunk of records."""
    try:
        await bulk_insert(db, TABLE_NAME, records)
    except Exception as e:
        print(f"A task failed: {e}")

async def main():
    """Main function to run the async stress test."""
    fake = Faker()
    db = AsyncMariaDB()
    await db.initialize()

    try:
        await setup_table(db)

        print(f"Generating {NUM_RECORDS} fake records...")
        all_records = [
            {"name": fake.name(), "email": fake.email(), "address": fake.address()}
            for _ in range(NUM_RECORDS)
        ]
        df = pd.DataFrame(all_records)
        
        # Split the DataFrame into chunks for each concurrent task
        record_chunks = [
            df.iloc[i * RECORDS_PER_TASK:(i + 1) * RECORDS_PER_TASK]
            for i in range(CONCURRENT_TASKS)
        ]

        print(f"Starting stress test with {CONCURRENT_TASKS} concurrent tasks...")
        start_time = time.perf_counter()

        # Create and run all concurrent tasks
        tasks = [run_insert_task(db, chunk) for chunk in record_chunks]
        await asyncio.gather(*tasks)

        end_time = time.perf_counter()
        total_time = end_time - start_time

        print("\n--- Stress Test Results ---")
        print(f"Total records inserted: {NUM_RECORDS}")
        print(f"Concurrent tasks: {CONCURRENT_TASKS}")
        print(f"Total time taken: {total_time:.4f} seconds")
        print(f"Inserts per second: {NUM_RECORDS / total_time:.2f}")

        # Verify the number of records in the database
        count_result = await db.fetch_one(f"SELECT COUNT(*) as count FROM {TABLE_NAME}")
        print(f"Verification: Found {count_result['count']} records in the table.")

    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(main())
