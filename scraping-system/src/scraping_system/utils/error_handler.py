"""
Database Error Handling Module

Provides comprehensive error handling for MongoDB operations
with custom exceptions and retry logic.
"""

import logging
from typing import Optional, Callable, Any
from functools import wraps
import asyncio
from datetime import datetime

from pymongo.errors import (
    ConnectionFailure,
    OperationFailure,
    DuplicateKeyError,
    BulkWriteError,
    ServerSelectionTimeoutError,
    NetworkTimeout,
    CursorNotFound,
    InvalidName,
    ConfigurationError,
    AutoReconnect
)

from src.scraping_system.monitoring.metrics import MetricsCollector

logger = logging.getLogger(__name__)


# ============================================
# Custom Exceptions
# ============================================

class DatabaseError(Exception):
    """Base exception for database errors."""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        self.message = message
        self.original_error = original_error
        self.timestamp = datetime.utcnow()
        super().__init__(self.message)


class ConnectionError(DatabaseError):
    """Raised when database connection fails."""
    pass


class DuplicateEntryError(DatabaseError):
    """Raised when attempting to insert duplicate entry."""
    pass


class QueryError(DatabaseError):
    """Raised when query execution fails."""
    pass


class ValidationError(DatabaseError):
    """Raised when data validation fails."""
    pass


class TimeoutError(DatabaseError):
    """Raised when operation times out."""
    pass


class AuthenticationError(DatabaseError):
    """Raised when authentication fails."""
    pass


class PermissionError(DatabaseError):
    """Raised when user lacks required permissions."""
    pass


# ============================================
# Error Handler
# ============================================

class DatabaseErrorHandler:
    """Handles database errors with retry logic and logging."""
    
    def __init__(self, max_retries: int = 3, initial_delay: float = 1.0):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        # Don't create metrics here to avoid duplicate registration
        # Metrics will be handled by the main application
    
    def handle_error(self, error: Exception, operation: str) -> None:
        """Handle database error and raise appropriate exception."""
        
        # Log error
        logger.error(f"Database error in {operation}: {error}", exc_info=True)
        
        # Map pymongo errors to custom exceptions
        if isinstance(error, ConnectionFailure):
            raise ConnectionError(
                f"Failed to connect to database: {error}",
                original_error=error
            )
        
        elif isinstance(error, ServerSelectionTimeoutError):
            raise ConnectionError(
                f"Database server selection timeout: {error}",
                original_error=error
            )
        
        elif isinstance(error, DuplicateKeyError):
            raise DuplicateEntryError(
                f"Duplicate entry detected: {error}",
                original_error=error
            )
        
        elif isinstance(error, BulkWriteError):
            # Extract details from bulk write error
            details = error.details if hasattr(error, 'details') else {}
            raise QueryError(
                f"Bulk write operation failed: {error}. Details: {details}",
                original_error=error
            )
        
        elif isinstance(error, OperationFailure):
            # Check if it's an authentication error
            if error.code == 18:  # Authentication failed
                raise AuthenticationError(
                    f"Database authentication failed: {error}",
                    original_error=error
                )
            # Check if it's a permission error
            elif error.code == 13:  # Unauthorized
                raise PermissionError(
                    f"Insufficient permissions: {error}",
                    original_error=error
                )
            else:
                raise QueryError(
                    f"Database operation failed: {error}",
                    original_error=error
                )
        
        elif isinstance(error, NetworkTimeout):
            raise TimeoutError(
                f"Network timeout: {error}",
                original_error=error
            )
        
        elif isinstance(error, CursorNotFound):
            raise QueryError(
                f"Cursor not found (connection may have been closed): {error}",
                original_error=error
            )
        
        elif isinstance(error, InvalidName):
            raise ValidationError(
                f"Invalid database name or collection name: {error}",
                original_error=error
            )
        
        elif isinstance(error, ConfigurationError):
            raise DatabaseError(
                f"Database configuration error: {error}",
                original_error=error
            )
        
        elif isinstance(error, asyncio.TimeoutError):
            raise TimeoutError(
                f"Operation timed out: {error}",
                original_error=error
            )
        
        elif isinstance(error, AutoReconnect):
            raise ConnectionError(
                f"Database connection lost: {error}",
                original_error=error
            )
        
        else:
            # Generic database error
            raise DatabaseError(
                f"Unexpected database error in {operation}: {error}",
                original_error=error
            )
    
    async def execute_with_retry(
        self,
        operation: Callable,
        operation_name: str,
        *args,
        **kwargs
    ) -> Any:
        """Execute database operation with retry logic."""
        
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                result = await operation(*args, **kwargs)
                
                # Log successful retry if it wasn't the first attempt
                if attempt > 0:
                    logger.info(
                        f"Operation '{operation_name}' succeeded on attempt {attempt + 1}"
                    )
                
                return result
                
            except (ConnectionError, TimeoutError, ServerSelectionTimeoutError) as e:
                # These errors might be transient, so retry
                last_error = e
                
                if attempt < self.max_retries - 1:
                    # Calculate exponential backoff
                    delay = self.initial_delay * (2 ** attempt)
                    
                    logger.warning(
                        f"Operation '{operation_name}' failed (attempt {attempt + 1}/{self.max_retries}): {e}. "
                        f"Retrying in {delay} seconds..."
                    )
                    
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Operation '{operation_name}' failed after {self.max_retries} attempts: {e}"
                    )
            
            except (DuplicateEntryError, ValidationError, AuthenticationError, PermissionError) as e:
                # These errors are not transient, don't retry
                logger.error(f"Non-retryable error in '{operation_name}': {e}")
                raise
            
            except Exception as e:
                # Unexpected error, wrap and raise
                last_error = self.handle_error(e, operation_name)
                raise last_error
        
        # If we get here, all retries failed
        if last_error:
            raise last_error
        else:
            raise DatabaseError(
                f"Operation '{operation_name}' failed after {self.max_retries} attempts",
                original_error=None
            )
    
    def retry_decorator(
        self,
        max_retries: Optional[int] = None,
        operation_name: Optional[str] = None
    ):
        """Decorator to add retry logic to database operations."""
        
        if max_retries is None:
            max_retries = self.max_retries
        
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                op_name = operation_name or func.__name__
                return await self.execute_with_retry(func, op_name, *args, **kwargs)
            
            return wrapper
        
        return decorator


# ============================================
# Context Manager for Database Operations
# ============================================

class DatabaseTransaction:
    """Context manager for database transactions."""
    
    def __init__(self, db_connection):
        self.db_connection = db_connection
        self.session = None
        self.error_handler = DatabaseErrorHandler()
    
    async def __aenter__(self):
        """Start a transaction."""
        try:
            # Start session
            self.session = await self.db_connection.client.start_session()
            
            # Start transaction
            self.session.start_transaction()
            
            logger.info("Database transaction started")
            
            return self.session
            
        except Exception as e:
            logger.error(f"Failed to start transaction: {e}")
            if self.session:
                await self.session.end_session()
            raise
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Commit or rollback transaction."""
        
        try:
            if exc_type is None:
                # No exception, commit transaction
                await self.session.commit_transaction()
                logger.info("Database transaction committed")
            else:
                # Exception occurred, rollback transaction
                await self.session.abort_transaction()
                logger.warning(
                    f"Database transaction rolled back due to: {exc_val}"
                )
                
        except Exception as e:
            logger.error(f"Error during transaction cleanup: {e}")
            
        finally:
            # End session
            if self.session:
                await self.session.end_session()
                logger.info("Database session ended")


# ============================================
# Health Check
# ============================================

class DatabaseHealthChecker:
    """Performs health checks on database connection."""
    
    def __init__(self, db_connection):
        self.db_connection = db_connection
        self.error_handler = DatabaseErrorHandler()
    
    async def check_connection(self) -> dict:
        """Check if database connection is healthy."""
        
        try:
            # Check if connected
            is_connected = await self.db_connection.is_connected()
            
            if not is_connected:
                return {
                    "status": "unhealthy",
                    "connected": False,
                    "error": "Not connected to database"
                }
            
            # Try to ping database
            await self.db_connection.client.admin.command('ping')
            
            # Get database stats
            stats = await self.db_connection.db.command('dbstats')
            
            return {
                "status": "healthy",
                "connected": True,
                "database": self.db_connection.db.name,
                "stats": {
                    "collections": stats.get('collections', 0),
                    "objects": stats.get('objects', 0),
                    "data_size": stats.get('dataSize', 0),
                    "storage_size": stats.get('storageSize', 0),
                    "indexes": stats.get('indexes', 0),
                    "index_size": stats.get('totalIndexSize', 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e)
            }
    
    async def check_collection_exists(self, collection_name: str) -> bool:
        """Check if a collection exists."""
        
        try:
            collections = await self.db_connection.db.list_collection_names()
            return collection_name in collections
            
        except Exception as e:
            logger.error(f"Failed to check collection '{collection_name}': {e}")
            return False
    
    async def check_index_exists(
        self,
        collection_name: str,
        index_name: str
    ) -> bool:
        """Check if an index exists on a collection."""
        
        try:
            collection = self.db_connection.db[collection_name]
            indexes = await collection.index_information()
            
            return index_name in indexes
            
        except Exception as e:
            logger.error(
                f"Failed to check index '{index_name}' on '{collection_name}': {e}"
            )
            return False


# ============================================
# Global Error Handler Instance
# ============================================

error_handler = DatabaseErrorHandler()


# ============================================
# Decorators and Context Managers
# ============================================

def retry_on_database_error(max_retries: int = 3, initial_delay: float = 1.0):
    """Decorator to retry database operations on failure.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries (exponential backoff)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except (ConnectionFailure, NetworkTimeout, AutoReconnect, ServerSelectionTimeoutError) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Database operation failed (attempt {attempt + 1}/{max_retries}): {e}. "
                            f"Retrying in {delay}s..."
                        )
                        await asyncio.sleep(delay)
                        delay *= 2  # Exponential backoff
                    else:
                        logger.error(f"Database operation failed after {max_retries} attempts: {e}")
                except Exception as e:
                    # Don't retry on other exceptions
                    logger.error(f"Non-retryable error in database operation: {e}")
                    raise
            
            # If we exhausted all retries
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (ConnectionFailure, NetworkTimeout, AutoReconnect, ServerSelectionTimeoutError) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Database operation failed (attempt {attempt + 1}/{max_retries}): {e}. "
                            f"Retrying in {delay}s..."
                        )
                        time.sleep(delay)
                        delay *= 2  # Exponential backoff
                    else:
                        logger.error(f"Database operation failed after {max_retries} attempts: {e}")
                except Exception as e:
                    # Don't retry on other exceptions
                    logger.error(f"Non-retryable error in database operation: {e}")
                    raise
            
            # If we exhausted all retries
            raise last_exception
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            import time
            return sync_wrapper
    
    return decorator


class DatabaseTransaction:
    """Context manager for database transactions."""
    
    def __init__(self, db_connection):
        self.db_connection = db_connection
        self.session = None
    
    async def __aenter__(self):
        """Enter transaction context."""
        if not self.db_connection.client:
            raise ConnectionError("Database not connected")
        
        self.session = await self.db_connection.client.start_session()
        self.session.start_transaction()
        logger.debug("Database transaction started")
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit transaction context."""
        try:
            if exc_type is None:
                # No exception, commit transaction
                await self.session.commit_transaction()
                logger.debug("Database transaction committed")
            else:
                # Exception occurred, abort transaction
                await self.session.abort_transaction()
                logger.debug("Database transaction aborted")
        except Exception as e:
            logger.error(f"Error in transaction cleanup: {e}")
            raise
        finally:
            if self.session:
                self.session.end_session()


def handle_database_transaction(func: Callable) -> Callable:
    """Decorator to handle database transactions automatically.
    
    Wraps a function in a database transaction, committing on success
    and rolling back on exception.
    """
    @wraps(func)
    async def wrapper(db_connection, *args, **kwargs):
        async with DatabaseTransaction(db_connection) as session:
            try:
                result = await func(db_connection, *args, session=session, **kwargs)
                await session.commit_transaction()
                return result
            except Exception as e:
                await session.abort_transaction()
                raise
    
    return wrapper
