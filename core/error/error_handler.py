"""Core error handler
Provides unified error handling, logging, and global exception capture functionality

Contains global error handling functions and global exception handler registration functionality.
"""

import sys
import threading
import types
from typing import Dict, Any, Optional, Callable, List, Type
from .formatter import ErrorFormatter
from core.logger import error as log_error_func, warning


class ErrorHandler:
    """Error handler - responsible for unified error handling and recording"""

    def __init__(self):
        self._handlers: List[Callable[[Exception, Optional[Dict[str, Any]]], bool]] = []
        self._lock = threading.Lock()
        self._default_context: Dict[str, Any] = {}

    def add_handler(
        self, handler: Callable[[Exception, Optional[Dict[str, Any]]], bool]
    ) -> None:
        """
        Add error handling callback

        Args:
            handler: Error handling callback function, returns True if handled, False to continue propagation
        """
        with self._lock:
            if handler not in self._handlers:
                self._handlers.append(handler)

    def remove_handler(
        self, handler: Callable[[Exception, Optional[Dict[str, Any]]], bool]
    ) -> None:
        """
        Remove error handling callback

        Args:
            handler: Error handling callback function to remove
        """
        with self._lock:
            if handler in self._handlers:
                self._handlers.remove(handler)

    def set_default_context(self, context: Dict[str, Any]) -> None:
        """
        Set default context for all error handling

        Args:
            context: Default context dictionary
        """
        with self._lock:
            self._default_context = context.copy()

    def get_handler_count(self) -> int:
        """Get the number of registered error handlers"""
        with self._lock:
            return len(self._handlers)

    def get_default_context(self) -> Dict[str, Any]:
        """Get the default context dictionary"""
        with self._lock:
            return self._default_context.copy()

    def handle_error(
        self, exception: Exception, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Handle error

        Args:
            exception: Exception object
            context: Error context information

        Returns:
            Whether the error was successfully handled
        """
        # Merge context
        full_context: Dict[str, Any] = {}
        with self._lock:
            full_context.update(self._default_context)
        if context:
            full_context.update(context)

        # Call custom handlers
        with self._lock:
            for handler in self._handlers:
                try:
                    if handler(exception, full_context):
                        return True
                except Exception as handler_error:
                    # Handler's own errors should not affect main flow
                    warning(f"Error handler failed: {handler_error}")

        # Default handling: log error
        self.log_error(exception, full_context)
        return True

    def log_error(
        self, exception: Exception, context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log error with formatted message

        Args:
            exception: Exception object to log
            context: Additional context information
        """
        formatted_error = ErrorFormatter.format_error(exception)
        if context:
            formatted_error += f"\nContext: {context}"
        log_error_func(formatted_error)


# Global error handler instance
_global_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """
    Get global error handler instance (singleton pattern)

    Returns:
        ErrorHandler: Global error handler instance
    """
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler


def handle_error(
    exception: Exception, context: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Global error handling function

    Args:
        exception: Exception object to handle
        context: Additional context information

    Returns:
        Whether the error was successfully handled
    """
    return get_error_handler().handle_error(exception, context)


def register_global_error_handler() -> None:
    """Register global error handler for unhandled exceptions"""

    def global_excepthook(
        exc_type: Type[BaseException],
        exc_value: Optional[BaseException],
        exc_traceback: Optional[types.TracebackType],
    ) -> None:
        """Global exception hook"""
        if issubclass(exc_type, KeyboardInterrupt):
            # Allow keyboard interrupt to exit normally
            if exc_value is not None:
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # Handle the exception using the global handler function
        # Only handle Exception types, not BaseException subclasses like SystemExit
        if exc_value is not None and isinstance(exc_value, Exception):
            handle_error(
                exc_value, {"global_handler": True, "traceback_obj": exc_traceback}
            )
        elif exc_value is not None:
            # For BaseException types that are not Exception, use default handler
            sys.__excepthook__(exc_type, exc_value, exc_traceback)

    # Set global exception handler
    sys.excepthook = global_excepthook
