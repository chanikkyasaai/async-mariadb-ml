# API Reference

This document provides a detailed reference for the classes and methods in the `async-mariadb-connector` library.

## `AsyncMariaDB` Class

The main class for interacting with the MariaDB database.

### `__init__(self, **kwargs)`

Initializes the connector. Configuration can be passed as keyword arguments or loaded from environment variables.

-   **Parameters:**
    -   `host` (str): Database host.
    -   `port` (int): Database port.
    -   `user` (str): Database username.
    -   `password` (str): Database password.
    -   `db` (str): Database name.
    -   `autocommit` (bool): Enable or disable autocommit. Default: `True`.
    -   `pool_minsize` (int): Minimum number of connections in the pool. Default: `1`.
    -   `pool_maxsize` (int): Maximum number of connections in the pool. Default: `10`.

### `async def initialize(self)`

Creates and initializes the connection pool. This must be called before any other database operations.

### `async def close(self)`

Closes the connection pool and releases all connections.

### `async def execute(self, query: str, params: tuple = None) -> int`

Executes a single SQL query (e.g., `INSERT`, `UPDATE`, `CREATE`).

-   **Parameters:**
    -   `query` (str): The SQL query to execute.
    -   `params` (tuple, optional): A tuple of parameters to be safely substituted into the query.
-   **Returns:** The number of affected rows.

### `async def executemany(self, query: str, params_list: List[tuple], commit: bool = True) -> int`

Executes a query with multiple parameter sets in a single batch operation. This is **much more efficient** than calling `execute()` in a loop.

-   **Parameters:**
    -   `query` (str): The SQL query with placeholders (e.g., `"INSERT INTO users (name, age) VALUES (%s, %s)"`).
    -   `params_list` (List[tuple]): A list of parameter tuples, one for each execution.
    -   `commit` (bool, optional): Whether to commit the transaction. Default: `True`.
-   **Returns:** Total number of affected rows.

**Example:**
```python
# Batch insert multiple users
data = [
    ("Alice", 25),
    ("Bob", 30),
    ("Charlie", 35)
]
rows = await db.executemany(
    "INSERT INTO users (name, age) VALUES (%s, %s)",
    data
)
print(f"Inserted {rows} rows")
```

**Performance Note:** For bulk operations, `executemany()` is significantly faster than a loop because it sends all data in a single batch to the database.

### `async def fetch_one(self, query: str, params: tuple = None) -> dict`

Executes a query and fetches the first result as a dictionary.

-   **Parameters:**
    -   `query` (str): The SQL query.
    -   `params` (tuple, optional): Parameters for the query.
-   **Returns:** A dictionary representing the row, or `None` if no result is found.

### `async def fetch_all(self, query: str, params: tuple = None) -> list[dict]`

Executes a query and fetches all results as a list of dictionaries.

-   **Parameters:**
    -   `query` (str): The SQL query.
    -   `params` (tuple, optional): Parameters for the query.
-   **Returns:** A list of dictionaries.

### `async def fetch_all_df(self, query: str, params: tuple = None) -> pd.DataFrame`

Executes a query and returns the results as a pandas DataFrame.

-   **Parameters:**
    -   `query` (str): The SQL query.
    -   `params` (tuple, optional): Parameters for the query.
-   **Returns:** A pandas DataFrame.

### `async def fetch_stream(self, query: str, params: tuple = None) -> AsyncGenerator[dict, None]`

Executes a query and streams the results one row at a time. This is useful for large datasets.

-   **Parameters:**
    -   `query` (str): The SQL query.
    -   `params` (tuple, optional): Parameters for the query.
-   **Yields:** A dictionary for each row in the result set.

## `bulk_insert` Function

### `async def bulk_insert(db: AsyncMariaDB, table_name: str, dataframe: pd.DataFrame)`

Performs a high-speed bulk insert of a pandas DataFrame into a table.

-   **Parameters:**
    -   `db` (AsyncMariaDB): An initialized `AsyncMariaDB` instance.
    -   `table_name` (str): The name of the target table.
    -   `dataframe` (pd.DataFrame): The DataFrame to insert.

## Exceptions

-   `ConnectionError`: Raised when the connector fails to establish a connection after multiple retries.
-   `BulkOperationError`: Raised if a bulk insert operation fails.
