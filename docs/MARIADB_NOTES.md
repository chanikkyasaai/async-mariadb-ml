# MariaDB Integration Notes

This document covers MariaDB-specific implementation details, tested configurations, and best practices for using `async-mariadb-connector`.

## Tested Environment

This library has been developed and tested against the following versions:

- **MariaDB Server:** 11.8.3
- **Python:** 3.9, 3.10, 3.11
- **Core Dependencies:**
  - `aiomysql`: 0.2.0 (underlying async MySQL/MariaDB driver)
  - `PyMySQL`: 1.1.2 (used in benchmarks for sync comparison)
  - `pandas`: 2.0.0+
  - `python-dotenv`: 1.0.0+
  - `tenacity`: 8.2.3+

## Character Set and Collation

The connector is designed to work with MariaDB's full Unicode support:

- **Default Character Set:** `utf8mb4`
- **Default Collation:** `utf8mb4_unicode_ci`
- **Emoji Support:** Full support for 4-byte UTF-8 characters including emojis

To ensure proper character handling, configure your MariaDB server with:

```sql
--character-set-server=utf8mb4
--collation-server=utf8mb4_unicode_ci
```

When creating databases and tables, explicitly specify:

```sql
CREATE DATABASE mydb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE mytable (
    id INT PRIMARY KEY,
    text VARCHAR(255)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

## SQL Mode

This connector is tested with MariaDB's strict SQL mode for data integrity:

```
STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION
```

This mode ensures:
- Invalid or missing values cause errors instead of warnings
- Zero dates (`0000-00-00`) are rejected
- Division by zero produces errors
- No automatic engine substitution

You can set this in `my.cnf` or docker-compose:

```ini
[mysqld]
sql-mode=STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION
```

## Data Types

### JSON Support

MariaDB's native JSON type is fully supported:

```python
import json
from async_mariadb_connector import AsyncMariaDB

async with AsyncMariaDB() as db:
    # Insert JSON data
    metadata = {"role": "admin", "verified": True, "tags": ["python", "async"]}
    await db.execute(
        "INSERT INTO users (name, metadata) VALUES (%s, %s)",
        ("Alice", json.dumps(metadata))
    )
    
    # Query JSON data
    result = await db.fetch_one("SELECT metadata FROM users WHERE name = %s", ("Alice",))
    data = json.loads(result['metadata'])
```

### DECIMAL Precision

MariaDB's `DECIMAL` type preserves exact precision for financial calculations:

```python
# Store monetary values with exact precision
await db.execute(
    "INSERT INTO accounts (user_id, balance) VALUES (%s, %s)",
    (1, Decimal("1234.56"))
)

# Fetch as DataFrame - DECIMAL columns are preserved
df = await db.fetch_all_df("SELECT * FROM accounts")
# df['balance'] will be pandas Decimal type
```

### NULL and NaN Handling

The library correctly handles SQL `NULL` and pandas `NaN`:

- **Fetching:** SQL `NULL` → Python `None` → pandas `NaN` (for numeric columns) or `None` (for object columns)
- **Bulk Insert:** pandas `NaN` → SQL `NULL`

```python
import pandas as pd
import numpy as np

# NaN values are converted to NULL on insert
df = pd.DataFrame({
    'user_id': [1, 2, 3],
    'score': [95.5, np.nan, 87.0]  # Middle value is NULL in database
})
await db.bulk_insert("test_scores", df)
```

### DateTime and Timezone

MariaDB stores `TIMESTAMP` values in UTC and converts them based on the session time zone:

```python
from datetime import datetime

# Insert datetime (assumes local timezone)
await db.execute(
    "INSERT INTO events (name, created_at) VALUES (%s, %s)",
    ("Login", datetime.now())
)

# Set session timezone if needed
await db.execute("SET time_zone = '+00:00'")  # UTC
```

**Best Practice:** Store all timestamps in UTC and handle timezone conversion in your application layer.

## Transactions and Autocommit

### Autocommit Mode (Default)

By default, the connector uses autocommit mode:

```python
db = AsyncMariaDB()  # autocommit=True by default
await db.execute("INSERT INTO users (name) VALUES ('Alice')")  # Auto-committed
```

### Manual Transactions

For multi-statement transactions, disable autocommit:

```python
db = AsyncMariaDB(autocommit=False)

try:
    await db.execute("START TRANSACTION")
    await db.execute("INSERT INTO accounts (user_id, balance) VALUES (1, 100)")
    await db.execute("INSERT INTO transactions (user_id, amount) VALUES (1, -100)")
    await db.execute("COMMIT")
except Exception as e:
    await db.execute("ROLLBACK")
    raise
```

Or use the `commit` parameter:

```python
await db.execute("INSERT INTO users (name) VALUES ('Bob')", commit=False)
await db.execute("INSERT INTO users (name) VALUES ('Charlie')", commit=False)
await db.execute("COMMIT")
```

## Connection Pooling

The connector uses `aiomysql.Pool` for efficient connection management:

- **Default Pool Size:** 1–10 connections
- **Automatic Reconnection:** Connections are validated and retried on failure
- **Configurable:**

```python
db = AsyncMariaDB(
    pool_minsize=5,   # Minimum idle connections
    pool_maxsize=20   # Maximum total connections
)
```

**Tuning Tips:**
- For high-concurrency web apps: `pool_maxsize=50–100`
- For batch processing: `pool_maxsize=10–20`
- Monitor with `SHOW PROCESSLIST` in MariaDB

## Performance Optimization

### Bulk Operations

Use `bulk_insert` for large DataFrame imports (10-100x faster than row-by-row):

```python
import pandas as pd

df = pd.read_csv("data.csv")  # 100k rows
await db.bulk_insert("staging_table", df, batch_size=5000)
```

### Streaming Large Results

For memory-efficient processing of large result sets:

```python
async for row in db.fetch_stream("SELECT * FROM large_table"):
    process_row(row)  # Process one row at a time
```

### Indexing

Ensure proper indexes for query performance:

```sql
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_created_at ON events(created_at);
```

## Docker Compose Setup

A reference `docker-compose.yml` is provided for local development:

```bash
docker-compose up -d
```

This spins up:
- MariaDB 11.8.3 on port `3307`
- Configured with `utf8mb4`, strict SQL mode
- Persistent volume for data
- Health checks for readiness

## Storage Engine

**InnoDB** (default) is recommended for:
- ACID compliance
- Row-level locking
- Foreign key constraints
- Crash recovery

```sql
CREATE TABLE mytable (
    id INT PRIMARY KEY,
    data TEXT
) ENGINE=InnoDB;
```

## Common Issues

### Connection Refused
- Verify MariaDB is running: `docker-compose ps` or `systemctl status mariadb`
- Check port: default is `3306`, docker-compose uses `3307`
- Verify `.env` configuration

### Character Encoding Errors
- Ensure database/tables use `utf8mb4`
- Check connection string includes `charset=utf8mb4`

### Slow Bulk Inserts
- Increase `batch_size` in `bulk_insert` (try 5000–10000)
- Disable indexes during import, rebuild after
- Use `LOAD DATA INFILE` for CSV imports > 1M rows

## Security Best Practices

- **Never commit `.env`** with credentials (add to `.gitignore`)
- Use environment variables for secrets
- Grant minimal privileges: `GRANT SELECT, INSERT ON mydb.* TO 'appuser'@'%'`
- Enable SSL/TLS for production: `ssl_ca`, `ssl_cert`, `ssl_key` in connection config
- Rotate passwords regularly

## Further Reading

- [MariaDB Documentation](https://mariadb.com/kb/en/)
- [aiomysql Documentation](https://aiomysql.readthedocs.io/)
- [Benchmarks](./BENCHMARKS.md) – Performance comparison vs synchronous connectors
