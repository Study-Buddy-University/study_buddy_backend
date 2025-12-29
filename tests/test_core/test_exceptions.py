"""Tests for custom exceptions"""

import pytest
from src.core.exceptions import (
    StudyBuddyException,
    NotFoundException,
    ValidationError,
    AuthenticationError,
    DatabaseError,
    LLMProviderError,
    VectorStoreError,
    DocumentProcessingError,
    FileProcessingError
)


@pytest.mark.unit
class TestCustomExceptions:
    """Test suite for custom exception classes"""
    
    def test_base_exception(self):
        """Test base StudyBuddyException"""
        exc = StudyBuddyException("Test error")
        assert str(exc) == "Test error"
        assert isinstance(exc, Exception)
    
    def test_not_found_exception(self):
        """Test NotFoundException"""
        exc = NotFoundException("Resource not found")
        assert str(exc) == "Resource not found"
        assert isinstance(exc, StudyBuddyException)
    
    def test_validation_error(self):
        """Test ValidationError"""
        exc = ValidationError("Invalid input")
        assert str(exc) == "Invalid input"
        assert isinstance(exc, StudyBuddyException)
    
    def test_authentication_error(self):
        """Test AuthenticationError"""
        exc = AuthenticationError("Auth failed")
        assert str(exc) == "Auth failed"
        assert isinstance(exc, StudyBuddyException)
    
    def test_database_error(self):
        """Test DatabaseError"""
        exc = DatabaseError("DB connection failed")
        assert str(exc) == "DB connection failed"
        assert isinstance(exc, StudyBuddyException)
    
    def test_llm_provider_error(self):
        """Test LLMProviderError"""
        exc = LLMProviderError("LLM API error")
        assert str(exc) == "LLM API error"
        assert isinstance(exc, StudyBuddyException)
    
    def test_file_processing_error(self):
        """Test FileProcessingError"""
        exc = FileProcessingError("File upload failed")
        assert str(exc) == "File upload failed"
        assert isinstance(exc, StudyBuddyException)
    
    def test_exception_inheritance_chain(self):
        """Test that all exceptions inherit properly"""
        exceptions = [
            NotFoundException,
            ValidationError,
            AuthenticationError,
            DatabaseError,
            LLMProviderError,
            FileProcessingError
        ]
        
        for exc_class in exceptions:
            exc = exc_class("test")
            assert isinstance(exc, StudyBuddyException)
            assert isinstance(exc, Exception)
