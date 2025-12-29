"""
Error Response Models and Handlers

Provides standardized error responses across the API with error codes,
request IDs for tracing, and proper HTTP status codes.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standardized error response format"""
    
    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[str] = Field(None, description="Additional error details")
    request_id: str = Field(..., description="Unique request identifier for tracing")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    path: Optional[str] = Field(None, description="API path where error occurred")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "VALIDATION_ERROR",
                "message": "Invalid request data",
                "details": "Field 'email' is required",
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2024-12-22T10:30:00Z",
                "path": "/api/v1/projects"
            }
        }
    
    @classmethod
    def create(
        cls,
        error_code: str,
        message: str,
        details: Optional[str] = None,
        path: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> "ErrorResponse":
        """Factory method to create error responses"""
        return cls(
            error_code=error_code,
            message=message,
            details=details,
            request_id=request_id or str(uuid4()),
            timestamp=datetime.utcnow(),
            path=path
        )


# Error Codes Enum
class ErrorCodes:
    """Standard error codes used across the API"""
    
    # 400 - Bad Request
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_FIELD = "MISSING_FIELD"
    
    # 401 - Unauthorized
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    
    # 403 - Forbidden
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    
    # 404 - Not Found
    NOT_FOUND = "NOT_FOUND"
    PROJECT_NOT_FOUND = "PROJECT_NOT_FOUND"
    DOCUMENT_NOT_FOUND = "DOCUMENT_NOT_FOUND"
    CONVERSATION_NOT_FOUND = "CONVERSATION_NOT_FOUND"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    
    # 409 - Conflict
    ALREADY_EXISTS = "ALREADY_EXISTS"
    DUPLICATE_ENTRY = "DUPLICATE_ENTRY"
    
    # 422 - Unprocessable Entity
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    UNSUPPORTED_FILE_TYPE = "UNSUPPORTED_FILE_TYPE"
    PROCESSING_ERROR = "PROCESSING_ERROR"
    
    # 429 - Too Many Requests
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # 500 - Internal Server Error
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    LLM_ERROR = "LLM_ERROR"
    VECTOR_STORE_ERROR = "VECTOR_STORE_ERROR"
    
    # 503 - Service Unavailable
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    DATABASE_UNAVAILABLE = "DATABASE_UNAVAILABLE"
