# Quick Start Guide

Get up and running with `async-mariadb-connector` in 3 minutes.

## Prerequisites

- Docker and Docker Compose (for local MariaDB)
- Python 3.9 or higher
- pip

## Step 1: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/chanikkyasaai/async-mariadb-ml.git
cd async-mariadb-ml

# Install the package
pip install -e ".[dev]"
```

## Step 2: Start MariaDB

```bash
# Start MariaDB 11.8.3 on port 3307
docker-compose up -d

# Check it's running
docker-compose ps
```

This creates:
- MariaDB server on `localhost:3307`
- Database: `test_db`
- User: `root` / Password: `root`
- Sample tables with data (users, products, embeddings)

## Step 3: Configure Environment

```bash
# Copy the example env file
cp .env.example .env

# The defaults match docker-compose, so no edits needed!
```

Your `.env` should contain:
```ini
DB_HOST=127.0.0.1
DB_PORT=3307
DB_USER=root
DB_PASSWORD=root
DB_NAME=test_db
```

## Step 4: Run Your First Query

Create `test_connection.py`:

```python
import asyncio
from async_mariadb_connector import AsyncMariaDB

async def main():
    async with AsyncMariaDB() as db:
        # Fetch sample users
        users = await db.fetch_all("SELECT * FROM users")
        print(f"Found {len(users)} users:")
        for user in users:
            print(f"  - {user['name']} ({user['email']})")

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
python test_connection.py
```

Expected output:
```
Found 3 users:
  - Alice Johnson (alice@example.com)
  - Bob Smith (bob@example.com)
  - Charlie Brown (charlie@example.com)
```

## Step 5: Try Examples

```bash
# Async DataFrame operations
python examples/demo_async_dataframe.py

# Bulk embeddings for RAG
python examples/demo_bulk_embeddings.py

# Streaming large datasets
python examples/demo_streaming.py

# Performance benchmark
python examples/benchmark_sync_vs_async.py
```

## Step 6: Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_mariadb_types.py -v
```

## Next Steps

- Read [MariaDB Integration Notes](./docs/MARIADB_NOTES.md) for type support and best practices
- Check [Benchmarks](./docs/BENCHMARKS.md) for performance data
- Review [API Reference](./docs/API_REFERENCE.md) for full method documentation
- Explore [examples/](./examples/) for more use cases

## Troubleshooting

**Can't connect to database:**
```bash
# Check MariaDB is running
docker-compose ps

# Check logs
docker-compose logs mariadb

# Restart
docker-compose restart mariadb
```

**Port already in use:**
```bash
# Edit docker-compose.yml to use a different port
ports:
  - "3308:3306"  # Use 3308 instead

# Update .env
DB_PORT=3308
```

**Permission denied:**
```bash
# On Linux/Mac, you may need sudo for docker commands
sudo docker-compose up -d
```

## Clean Up

```bash
# Stop MariaDB
docker-compose down

# Stop and remove data volume
docker-compose down -v
```
