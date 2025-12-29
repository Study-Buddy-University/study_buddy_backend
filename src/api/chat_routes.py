from typing import Callable, List
import logging

from fastapi import APIRouter, HTTPException, Request, Body
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

from src.models.schemas import ChatRequest, ChatResponse, ConversationResponse, MessageResponse
from src.services.chat_service import ChatService


def create_chat_routes(get_service: Callable[[], ChatService]) -> APIRouter:
    router = APIRouter()

    @router.post(
        "/chat",
        response_model=ChatResponse,
        summary="Send a chat message to AI assistant",
        description="""
        Send a message to the AI assistant within a project context.
        
        **Features:**
        - RAG with document context retrieval
        - Tool calling (calculator, web search)
        - Conversation history tracking
        - Streaming response support
        
        **Process:**
        1. Retrieves relevant documents from project
        2. Builds context with conversation history
        3. Calls LLM with tools if enabled
        4. Executes any tool calls
        5. Returns final response
        """,
        responses={
            200: {
                "description": "Successful response",
                "content": {
                    "application/json": {
                        "example": {
                            "conversation_id": 42,
                            "message": {
                                "id": 123,
                                "role": "user",
                                "content": "What is 2+2?",
                                "created_at": "2024-12-22T12:00:00Z"
                            },
                            "response": {
                                "id": 124,
                                "role": "assistant",
                                "content": "The answer is 4.",
                                "created_at": "2024-12-22T12:00:01Z"
                            }
                        }
                    }
                }
            },
            400: {"description": "Invalid request (missing fields, invalid project)"},
            404: {"description": "Project not found"},
            500: {"description": "Server error (LLM failure, database error)"},
        },
        tags=["Chat"],
    )
    async def chat(
        request: ChatRequest = Body(
            ...,
            examples=[
                {
                    "summary": "Simple chat",
                    "value": {
                        "project_id": 1,
                        "message": "What is 2+2?",
                    }
                },
                {
                    "summary": "Chat with history",
                    "value": {
                        "project_id": 1,
                        "message": "Tell me more about that",
                        "conversation_id": 42,
                    }
                },
                {
                    "summary": "Chat with documents",
                    "value": {
                        "project_id": 1,
                        "message": "Summarize these documents",
                        "document_ids": [1, 2, 3]
                    }
                },
                {
                    "summary": "Streaming chat",
                    "value": {
                        "project_id": 1,
                        "message": "Explain quantum physics",
                        "stream": True
                    }
                }
            ]
        )
    ):
        """
        Process a chat message and return AI response.
        
        Args:
            request: Chat request containing message and optional context
            
        Returns:
            ChatResponse with user message and AI-generated response
            
        Raises:
            HTTPException 400: Invalid request data
            HTTPException 404: Project not found
            HTTPException 500: Server error during processing
        """
        try:
            service = get_service()
            
            if request.stream:
                return StreamingResponse(
                    service.chat_stream(request),
                    media_type="text/event-stream"
                )
            
            response = await service.chat(request)
            return response
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get(
        "/conversations/{conversation_id}/messages",
        response_model=List[MessageResponse],
        summary="Get all messages in a conversation",
        description="""
        Retrieve all messages for a specific conversation, ordered chronologically.
        
        Messages include both user inputs and AI responses with metadata.
        """,
        responses={
            200: {
                "description": "List of messages",
                "content": {
                    "application/json": {
                        "example": [
                            {
                                "id": 1,
                                "role": "user",
                                "content": "Hello",
                                "created_at": "2024-12-22T12:00:00Z"
                            },
                            {
                                "id": 2,
                                "role": "assistant",
                                "content": "Hi! How can I help?",
                                "created_at": "2024-12-22T12:00:01Z"
                            }
                        ]
                    }
                }
            },
            500: {"description": "Server error"},
        },
        tags=["Chat"],
    )
    async def get_conversation_messages(conversation_id: int):
        """
        Get all messages for a conversation.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            List of MessageResponse objects ordered by created_at
            
        Raises:
            HTTPException 500: Server error
        """
        try:
            service = get_service()
            messages = service.message_repo.find_by_conversation(conversation_id)
            logger.info(f"Found {len(messages)} messages for conversation {conversation_id}")
            result = []
            for msg in messages:
                try:
                    validated = MessageResponse.model_validate(msg)
                    result.append(validated)
                except Exception as val_error:
                    logger.error(f"Validation error for message {msg.id}: {val_error}")
                    logger.error(f"Message data: {msg.__dict__}")
                    raise
            return result
        except Exception as e:
            logger.error(f"Error getting conversation messages: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @router.get(
        "/projects/{project_id}/conversations",
        response_model=List[ConversationResponse],
        summary="Get all conversations for a project",
        description="""
        Retrieve all conversations belonging to a specific project.
        
        Conversations are ordered by most recently updated first.
        """,
        responses={
            200: {
                "description": "List of conversations",
                "content": {
                    "application/json": {
                        "example": [
                            {
                                "id": 1,
                                "project_id": 1,
                                "title": "Math homework help",
                                "created_at": "2024-12-22T10:00:00Z",
                                "updated_at": "2024-12-22T12:00:00Z"
                            }
                        ]
                    }
                }
            },
            500: {"description": "Server error"},
        },
        tags=["Chat"],
    )
    async def get_project_conversations(project_id: int):
        """
        Get all conversations for a project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            List of ConversationResponse objects
            
        Raises:
            HTTPException 500: Server error (returns empty list)
        """
        try:
            logger.info(f"Fetching conversations for project {project_id}")
            service = get_service()
            conversations = service.conversation_repo.find_by_project(project_id)
            logger.info(f"Found {len(conversations)} conversations for project {project_id}")
            return [ConversationResponse.model_validate(conv) for conv in conversations]
        except Exception as e:
            logger.error(f"Failed to fetch conversations for project {project_id}: {e}", exc_info=True)
            return []

    @router.get(
        "/conversations/{conversation_id}",
        response_model=ConversationResponse,
        summary="Get conversation details",
        description="""
        Retrieve details for a specific conversation.
        
        Returns conversation metadata including title, timestamps, and token usage.
        """,
        responses={
            200: {
                "description": "Conversation details",
                "content": {
                    "application/json": {
                        "example": {
                            "id": 1,
                            "project_id": 1,
                            "title": "Math homework help",
                            "total_tokens": 1500,
                            "created_at": "2024-12-22T10:00:00Z",
                            "updated_at": "2024-12-22T12:00:00Z"
                        }
                    }
                }
            },
            404: {"description": "Conversation not found"},
            500: {"description": "Server error"},
        },
        tags=["Chat"],
    )
    async def get_conversation(conversation_id: int):
        """
        Get conversation by ID.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            ConversationResponse with metadata
            
        Raises:
            HTTPException 404: Conversation not found
            HTTPException 500: Server error
        """
        try:
            service = get_service()
            conversation = service.conversation_repo.find_by_id(conversation_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
            return ConversationResponse.model_validate(conversation)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.patch(
        "/conversations/{conversation_id}",
        response_model=ConversationResponse,
        summary="Update conversation title",
        description="""
        Update the title of a conversation.
        
        This allows users to rename conversations for better organization.
        """,
        responses={
            200: {"description": "Conversation updated successfully"},
            404: {"description": "Conversation not found"},
            500: {"description": "Server error"},
        },
        tags=["Chat"],
    )
    async def update_conversation(
        conversation_id: int,
        update_data: dict = Body(..., example={"title": "New conversation title"})
    ):
        """
        Update conversation title.
        
        Args:
            conversation_id: ID of the conversation to update
            update_data: Dictionary containing the new title
            
        Returns:
            Updated ConversationResponse
            
        Raises:
            HTTPException 404: Conversation not found
            HTTPException 400: Invalid update data
            HTTPException 500: Server error
        """
        try:
            service = get_service()
            conversation = service.conversation_repo.find_by_id(conversation_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            # Update title if provided
            if "title" in update_data:
                conversation.title = update_data["title"]
                updated = service.conversation_repo.update(conversation)
                logger.info(f"Updated conversation {conversation_id} title to: {update_data['title']}")
                return ConversationResponse.model_validate(updated)
            else:
                raise HTTPException(status_code=400, detail="No title provided")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating conversation {conversation_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @router.delete(
        "/conversations/{conversation_id}",
        summary="Delete a conversation",
        description="""
        Delete a conversation and all its messages.
        
        This action cannot be undone.
        """,
        responses={
            200: {"description": "Conversation deleted successfully"},
            404: {"description": "Conversation not found"},
            500: {"description": "Server error"},
        },
        tags=["Chat"],
    )
    async def delete_conversation(conversation_id: int):
        """
        Delete conversation by ID.
        
        Args:
            conversation_id: ID of the conversation to delete
            
        Returns:
            Success message
            
        Raises:
            HTTPException 404: Conversation not found
            HTTPException 500: Server error
        """
        try:
            service = get_service()
            conversation = service.conversation_repo.find_by_id(conversation_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            service.conversation_repo.delete(conversation_id)
            logger.info(f"Deleted conversation {conversation_id}")
            return {"message": "Conversation deleted successfully"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting conversation {conversation_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    return router
