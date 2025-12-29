"""Tests for ErrorResponse models"""

import pytest
from datetime import datetime
from src.core.error_response import ErrorResponse, ErrorCodes


@pytest.mark.unit
class TestErrorResponse:
    """Test suite for ErrorResponse model"""
    
    def test_create_error_response(self):
        """Test creating an error response"""
        error = ErrorResponse.create(
            error_code="TEST_ERROR",
            message="Test error message",
            details="Additional details"
        )
        
        assert error.error_code == "TEST_ERROR"
        assert error.message == "Test error message"
        assert error.details == "Additional details"
        assert error.request_id is not None
        assert isinstance(error.timestamp, datetime)
    
    def test_error_response_with_request_id(self):
        """Test error response with custom request ID"""
        error = ErrorResponse.create(
            error_code="TEST_ERROR",
            message="Test message",
            request_id="custom-id-123"
        )
        
        assert error.request_id == "custom-id-123"
    
    def test_error_response_with_path(self):
        """Test error response with path"""
        error = ErrorResponse.create(
            error_code="NOT_FOUND",
            message="Resource not found",
            path="/api/v1/projects/123"
        )
        
        assert error.path == "/api/v1/projects/123"
    
    def test_error_codes_constants(self):
        """Test that ErrorCodes has expected constants"""
        assert ErrorCodes.VALIDATION_ERROR == "VALIDATION_ERROR"
        assert ErrorCodes.NOT_FOUND == "NOT_FOUND"
        assert ErrorCodes.INTERNAL_ERROR == "INTERNAL_ERROR"
        assert ErrorCodes.DATABASE_ERROR == "DATABASE_ERROR"
        assert ErrorCodes.PROJECT_NOT_FOUND == "PROJECT_NOT_FOUND"
        assert ErrorCodes.DOCUMENT_NOT_FOUND == "DOCUMENT_NOT_FOUND"
    
    def test_error_response_serialization(self):
        """Test that error response can be serialized"""
        error = ErrorResponse.create(
            error_code="TEST_ERROR",
            message="Test message"
        )
        
        # Should be serializable to dict via model_dump()
        data = error.model_dump()
        
        assert isinstance(data, dict)
        assert data["error_code"] == "TEST_ERROR"
        assert data["message"] == "Test message"
        assert "request_id" in data
        assert "timestamp" in data
