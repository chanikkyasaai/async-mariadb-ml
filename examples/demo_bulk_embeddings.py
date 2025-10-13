# Async bulk insert example for embeddings
import asyncio
import pandas as pd
import numpy as np
from async_mariadb_connector import AsyncMariaDB, bulk_insert, BulkOperationError

async def main():
    """
    Connects to the database, creates a table for embeddings,
    generates sample embedding data, and performs a bulk insert.
    """
    try:
        async with AsyncMariaDB() as db:
            # Create a table for embeddings
            await db.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    vector BLOB,
                    text_content TEXT
                )
            """)

            # Generate sample data
            num_embeddings = 1000
            embedding_dim = 128
            
            data = {
                'vector': [np.random.rand(embedding_dim).astype(np.float32).tobytes() for _ in range(num_embeddings)],
                'text_content': [f'Sample text {i}' for i in range(num_embeddings)]
            }
            df = pd.DataFrame(data)

            print(f"Inserting {len(df)} embeddings...")
            await bulk_insert(db, 'embeddings', df)
            print("Bulk insert complete.")

            # Verify insertion
            count_result = await db.fetch("SELECT COUNT(*) as count FROM embeddings")
            print(f"Verification: Found {count_result[0]['count']} rows in embeddings table.")

            # Clean up the table
            await db.execute("DROP TABLE embeddings")

    except BulkOperationError as e:
        print(f"A bulk operation error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
