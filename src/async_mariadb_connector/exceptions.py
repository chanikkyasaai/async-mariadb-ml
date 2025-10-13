"""Custom exception classes for the async_mariadb library."""

class MariaDBError(Exception):
    """Base exception class for this library."""
    pass

class ConnectionError(MariaDBError):
    """Raised for connection-related errors."""
    pass

class QueryError(MariaDBError):
    """Raised for errors related to query execution."""
    pass

class BulkOperationError(MariaDBError):
    """Raised for errors during bulk operations."""
    pass
