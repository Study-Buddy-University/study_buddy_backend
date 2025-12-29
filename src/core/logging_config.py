"""
Logging Configuration

Sets up structured logging with JSON formatting for production
and readable formatting for development.
"""

import logging
import sys
from typing import Optional

from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields"""
    
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        
        # Add custom fields
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['timestamp'] = self.formatTime(record, self.datefmt)
        
        # Add extra fields if present
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id
        if hasattr(record, 'path'):
            log_record['path'] = record.path
        if hasattr(record, 'method'):
            log_record['method'] = record.method


def setup_logging(
    level: int = logging.INFO,
    json_format: bool = True,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Configure application logging
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Use JSON formatting (True for production, False for dev)
        log_file: Optional file path to write logs
        
    Returns:
        Configured logger instance
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    if json_format:
        # JSON formatting for production
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        # Human-readable formatting for development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Set levels for noisy libraries
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    # Log startup
    root_logger.info(
        "Logging configured",
        extra={
            'level': logging.getLevelName(level),
            'json_format': json_format,
            'log_file': log_file
        }
    )
    
    return root_logger


class RequestLogger:
    """Context manager for logging request-scoped information"""
    
    def __init__(self, logger: logging.Logger, request_id: str, **kwargs):
        self.logger = logger
        self.request_id = request_id
        self.extra = {'request_id': request_id, **kwargs}
    
    def debug(self, message: str, **kwargs):
        self.logger.debug(message, extra={**self.extra, **kwargs})
    
    def info(self, message: str, **kwargs):
        self.logger.info(message, extra={**self.extra, **kwargs})
    
    def warning(self, message: str, **kwargs):
        self.logger.warning(message, extra={**self.extra, **kwargs})
    
    def error(self, message: str, exc_info=False, **kwargs):
        self.logger.error(message, exc_info=exc_info, extra={**self.extra, **kwargs})
    
    def critical(self, message: str, exc_info=True, **kwargs):
        self.logger.critical(message, exc_info=exc_info, extra={**self.extra, **kwargs})
