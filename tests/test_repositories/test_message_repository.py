"""Tests for MessageRepository"""

import pytest
from src.models.database import Message
from src.repositories.message_repository import MessageRepository


@pytest.mark.unit
class TestMessageRepository:
    """Test suite for MessageRepository"""
    
    def test_create_message(self, message_repo: MessageRepository, test_conversation):
        """Test creating a new message"""
        message = Message(
            conversation_id=test_conversation.id,
            role="user",
            content="Test message",
            message_type="text",
        )
        
        created = message_repo.create(message)
        
        assert created.id is not None
        assert created.content == "Test message"
        assert created.role == "user"
        assert created.conversation_id == test_conversation.id
        assert created.created_at is not None
    
    def test_find_by_id(self, message_repo: MessageRepository, test_message):
        """Test finding message by ID"""
        found = message_repo.find_by_id(test_message.id)
        
        assert found is not None
        assert found.id == test_message.id
        assert found.content == test_message.content
    
    def test_find_by_conversation(self, message_repo: MessageRepository, test_db, test_conversation):
        """Test finding all messages in a conversation"""
        # Create multiple messages
        for i in range(3):
            msg = Message(
                conversation_id=test_conversation.id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i}",
                message_type="text"
            )
            test_db.add(msg)
        test_db.commit()
        
        messages = message_repo.find_by_conversation(test_conversation.id)
        
        assert len(messages) >= 3
        assert all(m.conversation_id == test_conversation.id for m in messages)
        # Should be ordered by created_at
        for i in range(len(messages) - 1):
            assert messages[i].created_at <= messages[i + 1].created_at
    
    def test_update_message(self, message_repo: MessageRepository, test_db, test_message):
        """Test updating a message"""
        test_message.content = "Updated content"
        test_db.commit()
        
        updated = message_repo.find_by_id(test_message.id)
        
        assert updated.content == "Updated content"
    
    def test_delete_message(self, message_repo: MessageRepository, test_db, test_conversation):
        """Test deleting a message"""
        message = Message(
            conversation_id=test_conversation.id,
            role="user",
            content="To delete",
            message_type="text"
        )
        created = message_repo.create(message)
        
        result = message_repo.delete(created.id)
        
        assert result is True
        assert message_repo.find_by_id(created.id) is None
    
    def test_message_ordering(self, message_repo: MessageRepository, test_db, test_conversation):
        """Test that messages are returned in chronological order"""
        import time
        
        # Create messages with slight delays
        message_ids = []
        for i in range(3):
            msg = Message(
                conversation_id=test_conversation.id,
                role="user",
                content=f"Message {i}",
                message_type="text"
            )
            created = message_repo.create(msg)
            message_ids.append(created.id)
            if i < 2:
                time.sleep(0.01)  # Small delay
        
        messages = message_repo.find_by_conversation(test_conversation.id)
        retrieved_ids = [m.id for m in messages]
        
        # Should be in chronological order
        assert retrieved_ids == message_ids
