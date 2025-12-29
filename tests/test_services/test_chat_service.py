"""Tests for ChatService"""

import pytest
from unittest.mock import MagicMock, AsyncMock

from src.services.chat_service import ChatService
from src.models.schemas import ChatRequest


@pytest.mark.unit
class TestChatService:
    """Test suite for ChatService"""
    
    @pytest.fixture
    def chat_service(
        self,
        mock_llm_provider,
        conversation_repo,
        message_repo,
        project_repo,
        mock_vector_store
    ):
        """Create ChatService with mocked dependencies"""
        return ChatService(
            llm_provider=mock_llm_provider,
            conversation_repo=conversation_repo,
            message_repo=message_repo,
            project_repo=project_repo,
            vector_store=mock_vector_store
        )
    
    @pytest.mark.asyncio
    async def test_chat_creates_new_conversation(
        self,
        chat_service,
        test_project,
        mock_llm_provider
    ):
        """Test that chat creates a new conversation when none exists"""
        request = ChatRequest(
            project_id=test_project.id,
            message="Hello, AI!",
            conversation_id=None,
            stream=False
        )
        
        response = await chat_service.chat(request)
        
        assert response.conversation_id is not None
        assert response.message.content == "Hello, AI!"
        assert response.message.role == "user"
        assert response.response.role == "assistant"
        mock_llm_provider.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_chat_uses_existing_conversation(
        self,
        chat_service,
        test_conversation,
        mock_llm_provider
    ):
        """Test that chat uses existing conversation"""
        request = ChatRequest(
            project_id=test_conversation.project_id,
            message="Follow-up question",
            conversation_id=test_conversation.id,
            stream=False
        )
        
        response = await chat_service.chat(request)
        
        assert response.conversation_id == test_conversation.id
        mock_llm_provider.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_chat_includes_conversation_history(
        self,
        chat_service,
        test_conversation,
        message_repo,
        mock_llm_provider
    ):
        """Test that conversation history is included in LLM context"""
        # Add some history
        from src.models.database import Message
        message_repo.create(Message(
            conversation_id=test_conversation.id,
            role="user",
            content="Previous question",
            message_type="text"
        ))
        message_repo.create(Message(
            conversation_id=test_conversation.id,
            role="assistant",
            content="Previous answer",
            message_type="text"
        ))
        
        request = ChatRequest(
            project_id=test_conversation.project_id,
            message="New question",
            conversation_id=test_conversation.id,
            stream=False
        )
        
        response = await chat_service.chat(request)
        
        # Verify LLM was called with history
        call_args = mock_llm_provider.generate.call_args
        messages_sent = call_args[0][0] if call_args else []
        
        # Should include system prompt + history + new message
        assert len(messages_sent) >= 3
        mock_llm_provider.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_chat_with_document_context(
        self,
        chat_service,
        test_project,
        test_document,
        mock_llm_provider,
        mock_vector_store
    ):
        """Test that document context is retrieved and included"""
        request = ChatRequest(
            project_id=test_project.id,
            message="Question about documents",
            document_ids=[test_document.id],
            stream=False
        )
        
        response = await chat_service.chat(request)
        
        # Verify response was generated
        assert response.conversation_id is not None
        assert response.message.content == "Question about documents"
        mock_llm_provider.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_chat_generates_title_for_new_conversation(
        self,
        chat_service,
        test_project,
        conversation_repo
    ):
        """Test that first message generates a conversation title"""
        request = ChatRequest(
            project_id=test_project.id,
            message="What is quantum computing?",
            conversation_id=None,
            stream=False
        )
        
        response = await chat_service.chat(request)
        
        # Find the created conversation
        conversation = conversation_repo.find_by_id(response.conversation_id)
        
        assert conversation is not None
        assert conversation.title is not None
        assert len(conversation.title) > 0
