#!/usr/bin/env python
"""
Error handling module for SmartBeauty RAG system.

This module provides custom exceptions and error handling utilities
for the RAG system to ensure graceful degradation when components fail.
"""
import sys
import logging
from typing import Optional, Callable, Any, Dict, Union
import functools
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Custom exceptions
class RAGSystemError(Exception):
    """Base class for RAG system exceptions."""
    pass

class DatabaseError(RAGSystemError):
    """Exception raised for database-related errors."""
    pass

class EmbeddingError(RAGSystemError):
    """Exception raised for embedding-related errors."""
    pass

class DataLoadingError(RAGSystemError):
    """Exception raised for data loading errors."""
    pass

class SearchError(RAGSystemError):
    """Exception raised for search-related errors."""
    pass

# Error handling decorator
def handle_errors(error_type: type = RAGSystemError, 
                 default_return: Any = None,
                 logger: Optional[logging.Logger] = None):
    """
    Decorator to handle errors in functions.
    
    Args:
        error_type: The type of error to catch
        default_return: The default value to return on error
        logger: Logger to use for logging errors
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            log = logger or logging.getLogger(func.__module__)
            try:
                return func(*args, **kwargs)
            except error_type as e:
                log.error(f"Error in {func.__name__}: {str(e)}")
                return default_return
            except Exception as e:
                log.error(f"Unexpected error in {func.__name__}: {str(e)}")
                log.debug(traceback.format_exc())
                raise
        return wrapper
    return decorator

# Context manager for database connections
class DatabaseConnection:
    """Context manager for database connections."""
    
    def __init__(self, connection_func):
        """
        Initialize the context manager.
        
        Args:
            connection_func: Function to create database connection
        """
        self.connection_func = connection_func
        self.conn = None
        
    def __enter__(self):
        """Enter the context manager."""
        try:
            self.conn = self.connection_func()
            return self.conn
        except Exception as e:
            raise DatabaseError(f"Failed to connect to database: {e}")
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        if self.conn:
            try:
                if exc_type:
                    self.conn.rollback()
                self.conn.close()
            except Exception as e:
                logging.error(f"Error closing database connection: {e}")
                
# Function to format error responses for API
def error_response(error: Exception, 
                  error_type: str = "general_error") -> Dict[str, Union[str, dict]]:
    """
    Format an error response for API endpoints.
    
    Args:
        error: The exception that occurred
        error_type: Type of error for categorization
        
    Returns:
        Dictionary with error details
    """
    return {
        "error": str(error),
        "error_type": error_type,
        "details": {
            "error_class": error.__class__.__name__
        }
    }

# Function to record errors for analytics
def record_error(error: Exception, 
                context: Dict[str, Any],
                logger: Optional[logging.Logger] = None) -> None:
    """
    Record error details for analytics and monitoring.
    
    Args:
        error: The exception that occurred
        context: Dictionary with context information
        logger: Logger to use
    """
    log = logger or logging.getLogger("error_analytics")
    error_details = {
        "error_type": error.__class__.__name__,
        "error_message": str(error),
        "context": context
    }
    log.error(f"Error occurred: {error_details}")
    # In a production system, this could send the error to a monitoring service
    # such as Sentry, Datadog, etc.
