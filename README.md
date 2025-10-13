# Async MariaDB Connector

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


A lightweight, production-grade, and asynchronous Python connector for MariaDB, designed for high-performance data operations in modern AI/ML and web applications.

## Overview

This library provides a simple yet powerful interface for interacting with MariaDB, built on top of `aiomysql`. It is tailored for data-intensive workflows that require high throughput, such as API backends, data processing pipelines, and AI applications. It offers seamless integration with pandas, robust error handling, and resilient connections.

## Key Features

-   **Asynchronous by Design:** Leverages `asyncio` for non-blocking database operations, enabling high concurrency.
-   **Connection Pooling:** Manages a pool of database connections for efficient and fast query execution.
-   **Pandas Integration:** Fetch data directly into pandas DataFrames and perform high-speed bulk inserts from them.
-   **Resilient and Robust:** Features automatic connection retries with exponential backoff to handle transient network or database issues.
-   **Memory-Efficient Streaming:** Includes a `fetch_stream` method to process large datasets row-by-row without loading everything into memory.
-   **Structured Logging & Custom Exceptions:** Provides clear logging for operations and a dedicated set of exceptions for precise error handling.
-   **Secure and Configurable:** Easily configure database credentials using environment variables.

## Installation

This package is not yet on PyPI, but you can install it directly from the source:

```bash
pip install .
```

## Quick Start

First, ensure your MariaDB connection details are set as environment variables in a `.env` file in your project root:

```ini
# .env
DB_HOST=127.0.0.1
DB_PORT=3307
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=your_db
```

Here's a simple example of how to connect and fetch data:

```python
import asyncio
import pandas as pd
from async_mariadb_connector import AsyncMariaDB

async def main():
    # The connector automatically loads .env file
    db = AsyncMariaDB()
    await db.initialize()

    try:
        # Create a table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255),
                age INT
            )
        """)

        # Insert some data
        await db.execute("INSERT INTO users (name, age) VALUES (%s, %s)", ("Alice", 30))

        # Fetch a single row
        user = await db.fetch_one("SELECT * FROM users WHERE name = %s", ("Alice",))
        print(f"Fetched one user: {user}")

        # Bulk insert from a DataFrame
        new_users_df = pd.DataFrame([
            {"name": "Bob", "age": 25},
            {"name": "Charlie", "age": 35}
        ])
        await db.bulk_insert("users", new_users_df)
        print("Bulk insert completed.")

        # Fetch all users into a DataFrame
        all_users_df = await db.fetch_all_df("SELECT * FROM users")
        print("All users:")
        print(all_users_df)

    finally:
        # Close the connection pool
        await db.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## Configuration

The `AsyncMariaDB` constructor accepts connection parameters directly or reads them from environment variables. The order of precedence is:
1.  Keyword arguments passed to the constructor (`host`, `port`, etc.).
2.  Environment variables.

| Argument / Variable | Default     | Description                   |
| ------------------- | ----------- | ----------------------------- |
| `host` / `DB_HOST`  | `127.0.0.1` | Database server host.         |
| `port` / `DB_PORT`  | `3306`      | Database server port.         |
| `user` / `DB_USER`  | `root`      | Database username.            |
| `password` / `DB_PASSWORD` | `""`   | Database password.            |
| `db` / `DB_NAME`    | `None`      | Database name.                |
| `autocommit`        | `True`      | Autocommit transactions.      |
| `pool_minsize`      | `1`         | Minimum connections in pool.  |
| `pool_maxsize`      | `10`        | Maximum connections in pool.  |

## API Reference

For detailed information on all methods and classes, please see the API reference in the `/docs` directory.

## Running Tests

To run the test suite, first install the development dependencies:

```bash
pip install -e ".[dev]"
```

Then, run pytest:

```bash
pytest
```

## Connect with the Author

This project was created by **Chanikya Nelapatla**.

-   **LinkedIn:** [https://www.linkedin.com/in/chanikkyasaai/](https://www.linkedin.com/in/chanikkyasaai/)
-   **GitHub:** [https://github.com/chanikkyasaai](https://github.com/chanikkyasaai)

## License

This project is licensed under the MIT License.
