"""Tests for ConversationRepository"""

import pytest
from src.models.database import Conversation
from src.repositories.conversation_repository import ConversationRepository


@pytest.mark.unit
class TestConversationRepository:
    """Test suite for ConversationRepository"""
    
    def test_create_conversation(self, conversation_repo: ConversationRepository, test_project):
        """Test creating a new conversation"""
        conversation = Conversation(
            project_id=test_project.id,
            title="Test Conversation",
            total_tokens=100,
        )
        
        created = conversation_repo.create(conversation)
        
        assert created.id is not None
        assert created.title == "Test Conversation"
        assert created.project_id == test_project.id
        assert created.total_tokens == 100
        assert created.created_at is not None
    
    def test_find_by_id(self, conversation_repo: ConversationRepository, test_conversation):
        """Test finding conversation by ID"""
        found = conversation_repo.find_by_id(test_conversation.id)
        
        assert found is not None
        assert found.id == test_conversation.id
        assert found.title == test_conversation.title
    
    def test_find_by_project(self, conversation_repo: ConversationRepository, test_db, test_project, conversation_factory):
        """Test finding all conversations for a project"""
        # Create multiple conversations
        conversation_factory.create(test_db, test_project.id, title="Conv 1")
        conversation_factory.create(test_db, test_project.id, title="Conv 2")
        conversation_factory.create(test_db, test_project.id, title="Conv 3")
        
        conversations = conversation_repo.find_by_project(test_project.id)
        
        assert len(conversations) >= 3
        assert all(c.project_id == test_project.id for c in conversations)
        # Should be ordered by updated_at DESC
        assert conversations[0].updated_at >= conversations[-1].updated_at
    
    def test_get_or_create_existing(self, conversation_repo: ConversationRepository, test_conversation):
        """Test get_or_create with existing conversation"""
        result = conversation_repo.get_or_create(
            project_id=test_conversation.project_id,
            conversation_id=test_conversation.id
        )
        
        assert result.id == test_conversation.id
        assert result.title == test_conversation.title
    
    def test_get_or_create_new(self, conversation_repo: ConversationRepository, test_project):
        """Test get_or_create creates new conversation"""
        result = conversation_repo.get_or_create(
            project_id=test_project.id,
            conversation_id=None,
            title="New Conversation"
        )
        
        assert result.id is not None
        assert result.project_id == test_project.id
        assert result.title == "New Conversation"
    
    def test_update_conversation(self, conversation_repo: ConversationRepository, test_conversation):
        """Test updating a conversation"""
        test_conversation.title = "Updated Title"
        test_conversation.total_tokens = 500
        
        updated = conversation_repo.update(test_conversation)
        
        assert updated.title == "Updated Title"
        assert updated.total_tokens == 500
    
    def test_delete_conversation(self, conversation_repo: ConversationRepository, test_db, test_project):
        """Test deleting a conversation"""
        conversation = Conversation(project_id=test_project.id, title="To Delete")
        created = conversation_repo.create(conversation)
        
        result = conversation_repo.delete(created.id)
        
        assert result is True
        assert conversation_repo.find_by_id(created.id) is None
