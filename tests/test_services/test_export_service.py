"""Tests for ExportService"""

import pytest
from src.services.export_service import ExportService
from src.models.database import Message


@pytest.mark.unit
class TestExportService:
    """Test suite for ExportService"""
    
    @pytest.fixture
    def export_service(self, conversation_repo, message_repo):
        """Create ExportService with repositories"""
        return ExportService(
            conversation_repo=conversation_repo,
            message_repo=message_repo
        )
    
    def test_export_service_has_repos(
        self,
        export_service
    ):
        """Test that export service has necessary repositories"""
        assert export_service.conversation_repo is not None
        assert export_service.message_repo is not None
    
    def test_get_conversation_messages(
        self,
        export_service,
        test_conversation,
        test_db
    ):
        """Test getting messages for export"""
        # Add some messages
        messages = [
            Message(
                conversation_id=test_conversation.id,
                role="user",
                content="Hello AI",
                message_type="text"
            ),
            Message(
                conversation_id=test_conversation.id,
                role="assistant",
                content="Hello! How can I help?",
                message_type="text"
            ),
        ]
        for msg in messages:
            test_db.add(msg)
        test_db.commit()
        
        # Get messages via repo
        retrieved_messages = export_service.message_repo.find_by_conversation(test_conversation.id)
        
        assert len(retrieved_messages) >= 2
        assert any("Hello AI" in m.content for m in retrieved_messages)
    
    def test_get_conversation_for_export(
        self,
        export_service,
        test_conversation
    ):
        """Test getting conversation for export"""
        conversation = export_service.conversation_repo.find_by_id(test_conversation.id)
        
        assert conversation is not None
        assert conversation.id == test_conversation.id
