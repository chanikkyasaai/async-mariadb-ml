# Demo for streaming large datasets
import asyncio
from async_mariadb_connector import AsyncMariaDB

async def main():
    """
    Demonstrates streaming query results for large datasets to conserve memory.
    """
    print("--- Streaming Demo ---")
    try:
        async with AsyncMariaDB() as db:
            # Create a table and insert a large number of rows
            await db.execute("CREATE TABLE IF NOT EXISTS large_table (id INT, name VARCHAR(50))")
            
            # Use a transaction for bulk inserts
            await db.execute("START TRANSACTION")
            for i in range(10000):
                await db.execute("INSERT INTO large_table (id, name) VALUES (%s, %s)", (i, f"Name_{i}"), commit=False)
            await db.execute("COMMIT")

            print("Inserted 10,000 rows.")

            # Stream results instead of fetching all at once
            print("Streaming results...")
            row_count = 0
            async for row in db.fetch_stream("SELECT * FROM large_table"):
                if row_count < 5:
                    print(f"  - Fetched row: {row}")
                row_count += 1
            
            print(f"Total rows streamed: {row_count}")

            # Clean up
            await db.execute("DROP TABLE large_table")
            print("--- Streaming Demo Complete ---")

    except Exception as e:
        print(f"An error occurred during the streaming demo: {e}")

if __name__ == "__main__":
    asyncio.run(main())
