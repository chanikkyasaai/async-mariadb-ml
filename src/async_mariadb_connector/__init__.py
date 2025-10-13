"""Async MariaDB Connector - A lightweight, async-enabled Python library for MariaDB."""

__version__ = "0.1.0"

from .core import AsyncMariaDB
from .dataframe import to_dataframe
from .bulk import bulk_insert
from .config import load_config
from .exceptions import MariaDBError, ConnectionError, QueryError, BulkOperationError

__all__ = [
    "AsyncMariaDB",
    "to_dataframe",
    "bulk_insert",
    "load_config",
    "MariaDBError",
    "ConnectionError",
    "QueryError",
    "BulkOperationError",
]
