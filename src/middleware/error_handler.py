"""
Error Handler Middleware

Centralized error handling for the FastAPI application.
Catches exceptions and returns standardized error responses.
"""

import logging
from typing import Callable

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.exceptions import (
    AuthenticationError,
    DatabaseError,
    DocumentProcessingError,
    FileProcessingError,
    LLMProviderError,
    NotFoundException,
    StudyBuddyException,
    ValidationError,
    VectorStoreError,
)
from src.core.error_response import ErrorCodes, ErrorResponse

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware to handle exceptions and return standardized error responses"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        try:
            return await call_next(request)
        
        except ValidationError as e:
            logger.warning(
                f"Validation error on {request.url.path}: {e}",
                extra={"path": request.url.path, "method": request.method}
            )
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=ErrorResponse.create(
                    error_code=ErrorCodes.VALIDATION_ERROR,
                    message="Invalid request data",
                    details=str(e),
                    path=str(request.url.path)
                ).model_dump()
            )
        
        except NotFoundException as e:
            logger.info(
                f"Resource not found on {request.url.path}: {e}",
                extra={"path": request.url.path, "method": request.method}
            )
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse.create(
                    error_code=ErrorCodes.NOT_FOUND,
                    message=str(e) or "Resource not found",
                    path=str(request.url.path)
                ).model_dump()
            )
        
        except AuthenticationError as e:
            logger.warning(
                f"Authentication error on {request.url.path}: {e}",
                extra={"path": request.url.path, "method": request.method}
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=ErrorResponse.create(
                    error_code=ErrorCodes.AUTHENTICATION_REQUIRED,
                    message="Authentication required",
                    details=str(e),
                    path=str(request.url.path)
                ).model_dump()
            )
        
        except FileProcessingError as e:
            logger.error(
                f"File processing error on {request.url.path}: {e}",
                extra={"path": request.url.path, "method": request.method}
            )
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content=ErrorResponse.create(
                    error_code=ErrorCodes.PROCESSING_ERROR,
                    message="Failed to process file",
                    details=str(e),
                    path=str(request.url.path)
                ).model_dump()
            )
        
        except DocumentProcessingError as e:
            logger.error(
                f"Document processing error on {request.url.path}: {e}",
                extra={"path": request.url.path, "method": request.method}
            )
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content=ErrorResponse.create(
                    error_code=ErrorCodes.PROCESSING_ERROR,
                    message="Failed to process document",
                    details=str(e),
                    path=str(request.url.path)
                ).model_dump()
            )
        
        except DatabaseError as e:
            logger.error(
                f"Database error on {request.url.path}: {e}",
                exc_info=True,
                extra={"path": request.url.path, "method": request.method}
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=ErrorResponse.create(
                    error_code=ErrorCodes.DATABASE_ERROR,
                    message="Database operation failed",
                    details="An error occurred while accessing the database",
                    path=str(request.url.path)
                ).model_dump()
            )
        
        except LLMProviderError as e:
            logger.error(
                f"LLM provider error on {request.url.path}: {e}",
                exc_info=True,
                extra={"path": request.url.path, "method": request.method}
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=ErrorResponse.create(
                    error_code=ErrorCodes.LLM_ERROR,
                    message="AI service temporarily unavailable",
                    details="Failed to communicate with the AI service",
                    path=str(request.url.path)
                ).model_dump()
            )
        
        except VectorStoreError as e:
            logger.error(
                f"Vector store error on {request.url.path}: {e}",
                exc_info=True,
                extra={"path": request.url.path, "method": request.method}
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=ErrorResponse.create(
                    error_code=ErrorCodes.VECTOR_STORE_ERROR,
                    message="Search service temporarily unavailable",
                    details="Failed to communicate with the search service",
                    path=str(request.url.path)
                ).model_dump()
            )
        
        except StudyBuddyException as e:
            # Catch-all for custom exceptions
            logger.error(
                f"Application error on {request.url.path}: {e}",
                exc_info=True,
                extra={"path": request.url.path, "method": request.method}
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=ErrorResponse.create(
                    error_code=ErrorCodes.INTERNAL_ERROR,
                    message="An unexpected error occurred",
                    details=str(e) if logger.level <= logging.DEBUG else None,
                    path=str(request.url.path)
                ).model_dump()
            )
        
        except Exception as e:
            # Unhandled exceptions
            logger.error(
                f"Unhandled exception on {request.url.path}: {e}",
                exc_info=True,
                extra={"path": request.url.path, "method": request.method}
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=ErrorResponse.create(
                    error_code=ErrorCodes.INTERNAL_ERROR,
                    message="An unexpected error occurred",
                    details="Please contact support if this persists",
                    path=str(request.url.path)
                ).model_dump()
            )
