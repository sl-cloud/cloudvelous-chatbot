"""
Structured logging configuration using loguru.
"""

import sys
import uuid
from contextvars import ContextVar
from functools import wraps
from typing import Any, Callable

from loguru import logger
from fastapi import Request


# Context variable for request ID
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def configure_logging(log_level: str = "INFO", json_logs: bool = False) -> None:
    """
    Configure loguru logger for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: Whether to output logs in JSON format
    """
    # Remove default logger
    logger.remove()

    # Add custom logger with format
    if json_logs:
        # JSON format for production
        logger.add(
            sys.stdout,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra[request_id]} | {name}:{function}:{line} | {message}",
            level=log_level,
            serialize=True,
        )
    else:
        # Human-readable format for development
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{extra[request_id]}</cyan> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
            level=log_level,
            colorize=True,
        )

    # Add request_id to all log records
    logger.configure(extra={"request_id": ""})


def get_logger(name: str = None):
    """
    Get a logger instance with request context.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance with request_id context
    """
    request_id = request_id_var.get("")
    return logger.bind(request_id=request_id, name=name or "app")


async def add_request_id_middleware(request: Request, call_next):
    """
    FastAPI middleware to add request ID to all logs.

    Args:
        request: FastAPI request object
        call_next: Next middleware in chain

    Returns:
        Response from next middleware
    """
    # Generate or extract request ID
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    # Set request ID in context var
    request_id_var.set(request_id)

    # Bind to logger
    with logger.contextualize(request_id=request_id):
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


def log_function_call(func: Callable) -> Callable:
    """
    Decorator to log function entry and exit.

    Args:
        func: Function to decorate

    Returns:
        Decorated function
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        log = get_logger(func.__module__)
        log.debug(f"Entering {func.__name__}", function=func.__name__)
        try:
            result = await func(*args, **kwargs)
            log.debug(f"Exiting {func.__name__}", function=func.__name__)
            return result
        except Exception as e:
            log.error(f"Error in {func.__name__}: {str(e)}", function=func.__name__, error=str(e))
            raise

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        log = get_logger(func.__module__)
        log.debug(f"Entering {func.__name__}", function=func.__name__)
        try:
            result = func(*args, **kwargs)
            log.debug(f"Exiting {func.__name__}", function=func.__name__)
            return result
        except Exception as e:
            log.error(f"Error in {func.__name__}: {str(e)}", function=func.__name__, error=str(e))
            raise

    # Return appropriate wrapper based on function type
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def log_service_operation(operation_name: str):
    """
    Decorator to log service operations with timing.

    Args:
        operation_name: Name of the operation being logged

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            import time
            log = get_logger(func.__module__)

            start_time = time.time()
            log.info(f"Starting {operation_name}", operation=operation_name)

            try:
                result = await func(*args, **kwargs)
                elapsed_ms = (time.time() - start_time) * 1000
                log.info(
                    f"Completed {operation_name}",
                    operation=operation_name,
                    duration_ms=round(elapsed_ms, 2)
                )
                return result
            except Exception as e:
                elapsed_ms = (time.time() - start_time) * 1000
                log.error(
                    f"Failed {operation_name}: {str(e)}",
                    operation=operation_name,
                    duration_ms=round(elapsed_ms, 2),
                    error=str(e)
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            import time
            log = get_logger(func.__module__)

            start_time = time.time()
            log.info(f"Starting {operation_name}", operation=operation_name)

            try:
                result = func(*args, **kwargs)
                elapsed_ms = (time.time() - start_time) * 1000
                log.info(
                    f"Completed {operation_name}",
                    operation=operation_name,
                    duration_ms=round(elapsed_ms, 2)
                )
                return result
            except Exception as e:
                elapsed_ms = (time.time() - start_time) * 1000
                log.error(
                    f"Failed {operation_name}: {str(e)}",
                    operation=operation_name,
                    duration_ms=round(elapsed_ms, 2),
                    error=str(e)
                )
                raise

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Initialize logging on module import
configure_logging()
