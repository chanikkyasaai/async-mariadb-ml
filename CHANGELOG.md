# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.2] - 2025-10-22

### Added
- **`executemany()` method** for efficient batch operations
  - Enables batch inserts of 2,900+ documents/sec
  - Replaces complex manual pool access with simple one-line API
  - Example: `await db.executemany("INSERT INTO users VALUES (%s, %s)", data)`
  
- **`get_pool_stats()` method** for connection pool monitoring
  - Returns pool metrics: size, max_size, in_use, available connections
  - Enables production monitoring and capacity planning
  - Example: `stats = db.get_pool_stats()`

- **New AI/ML-focused demo scripts**:
  - `examples/demo_json_performance.py` - JSON storage for embeddings (13% faster than PostgreSQL)
  - `examples/demo_hybrid_search.py` - FULLTEXT + vector similarity for RAG (33% faster)

- **LangChain integration files** in `langchain_pr/` directory for upstream PR submission

### Changed
- **Simplified API**: Removed unnecessary complexity, focusing on essential features
- **Enhanced Documentation**: Clearer explanations, code snippets, and usage examples
- Focused library on core async database operations for AI/ML use cases

### Fixed
- Updated notebook examples to use new `executemany()` API
- Improved error handling in `get_pool_stats()` when pool is not initialized

### Performance
- Batch insert: 2,900+ docs/sec
- JSON queries: 13% faster than PostgreSQL  
- Full-text search: 33% faster than PostgreSQL

### Tests
- All 26 tests passing ✅
- Added `test_executemany()` and `test_get_pool_stats()`

## [0.1.1] - 2025-10-21

### Fixed
- Updated documentation links in README.md to use absolute GitHub URLs instead of relative paths
- This fixes 404 errors when viewing documentation links from the PyPI package page

## [0.1.0] - 2025-10-21

### Added
- **Async Connection Pooling**: Automatic connection pool management with configurable min/max size
- **High-Level API**: Simple async methods (`execute`, `fetch_one`, `fetch_all`, `fetch_stream`)
- **Pandas Integration**: 
  - `fetch_all_df()` to fetch query results as DataFrame
  - `bulk_insert()` for high-speed DataFrame → MariaDB bulk operations
- **Retry Logic**: Automatic exponential backoff retries on connection failures (via tenacity)
- **Streaming Support**: Memory-efficient `fetch_stream()` for processing large result sets row-by-row
- **Production Features**:
  - Structured logging with configurable levels
  - Custom exception hierarchy (ConnectionError, QueryError, BulkOperationError)
  - Environment variable configuration via .env files
  - Context manager support (`async with AsyncMariaDB()`)
- **MariaDB-Specific Support**:
  - JSON column type handling
  - DECIMAL precision preservation
  - NULL/NaN conversion between pandas and SQL
  - utf8mb4 character set (full emoji support)
  - Timezone-aware datetime handling
- **Testing**: 24 comprehensive tests covering core functionality, edge cases, and MariaDB types (85% coverage)
- **Docker Setup**: docker-compose.yml for one-command local MariaDB environment
- **Documentation**:
  - Complete API reference
  - MariaDB integration notes with tested versions and best practices
  - Quick start guide
  - Benchmark results vs synchronous connectors (~30% faster on concurrent reads)
  - Example scripts for common use cases (RAG, streaming, bulk ops, LangChain)

### Technical Details
- Built on `aiomysql` 0.2.0 for async MySQL/MariaDB protocol
- Tested against MariaDB 11.8.3
- Compatible with Python 3.8, 3.9, 3.10, 3.11
- Dependencies: aiomysql, pandas, python-dotenv, tenacity

### Release Notes
This is the initial public release of async-mariadb-connector, designed for the MariaDB Python Hackathon (Integration Track). The library provides a production-ready, high-level async interface for MariaDB with a focus on performance, reliability, and ease of use for modern AI/ML and web applications.

---

## Release Process

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR** version (X.0.0): Incompatible API changes
- **MINOR** version (0.X.0): New features, backwards-compatible
- **PATCH** version (0.0.X): Bug fixes, backwards-compatible

### How to Release

1. Update version in `pyproject.toml`
2. Update this CHANGELOG.md with new version section
3. Commit changes: `git commit -am "Release vX.Y.Z"`
4. Create git tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
5. Push tag: `git push origin vX.Y.Z`
6. Build: `python -m build`
7. Upload to PyPI: `twine upload dist/*`
8. Create GitHub Release with changelog excerpt
