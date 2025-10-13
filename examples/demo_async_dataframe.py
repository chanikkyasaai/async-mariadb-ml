# Demo for fetching data asynchronously into a Pandas DataFrame
import asyncio
import pandas as pd
from async_mariadb_connector import AsyncMariaDB, to_dataframe, QueryError

async def main():
    """
    Connects to the database, creates a table, inserts data,
    and fetches it into a Pandas DataFrame.
    """
    try:
        async with AsyncMariaDB() as db:
            # Create a table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255),
                    email VARCHAR(255)
                )
            """)

            # Insert some data
            await db.execute("INSERT INTO users (name, email) VALUES (%s, %s)", ("Alice", "alice@example.com"))
            await db.execute("INSERT INTO users (name, email) VALUES (%s, %s)", ("Bob", "bob@example.com"))

            # Fetch data into a DataFrame
            data = await db.fetch("SELECT * FROM users")
            df = await to_dataframe(data)
            
            print("Data fetched into DataFrame:")
            print(df)

            # Clean up the table
            await db.execute("DROP TABLE users")

    except QueryError as e:
        print(f"A query error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
