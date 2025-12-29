from typing import Callable

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from src.models.schemas import ChatRequest, VoiceTranscribeResponse
from src.services.chat_service import ChatService
from src.services.voice_service import VoiceService


def create_voice_routes(
    get_voice_service: Callable[[], VoiceService],
    get_chat_service: Callable[[], ChatService],
) -> APIRouter:
    router = APIRouter()

    @router.post(
        "/voice/transcribe",
        response_model=VoiceTranscribeResponse,
        summary="Transcribe audio to text",
        description="""
        Convert audio file to text using Whisper speech recognition.
        
        **Supported formats:** WAV, MP3, M4A, FLAC, OGG
        
        **Model:** OpenAI Whisper (configurable size)
        """,
        responses={
            200: {"description": "Transcription successful"},
            400: {"description": "Invalid audio file"},
            500: {"description": "Server error"},
        },
        tags=["Voice"],
    )
    async def transcribe_audio(
        file: UploadFile = File(..., description="Audio file to transcribe"),
        language: str = None,
    ):
        """Transcribe audio file to text using Whisper."""
        try:
            if not file.content_type or not file.content_type.startswith("audio/"):
                raise HTTPException(
                    status_code=400,
                    detail="File must be an audio file"
                )
            
            voice_service = get_voice_service()
            transcription = await voice_service.transcribe_audio(file.file, language)
            
            return VoiceTranscribeResponse(
                transcription=transcription,
                conversation_id=None
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.post(
        "/voice/chat",
        summary="Voice chat with AI assistant",
        description="""
        Send voice message to AI assistant (transcribe + chat).
        
        **Process:**
        1. Transcribe audio to text
        2. Send text to chat service
        3. Return AI response
        
        **Supports streaming responses.**
        """,
        responses={
            200: {"description": "Chat response"},
            400: {"description": "Invalid audio file"},
            500: {"description": "Server error"},
        },
        tags=["Voice"],
    )
    async def voice_chat(
        project_id: int,
        file: UploadFile = File(..., description="Audio file with question"),
        conversation_id: int = None,
        language: str = None,
    ):
        """Voice chat: transcribe audio and get AI response."""
        try:
            voice_service = get_voice_service()
            
            transcription = await voice_service.transcribe_audio(file.file, language)
            
            chat_service = get_chat_service()
            chat_request = ChatRequest(
                project_id=project_id,
                conversation_id=conversation_id,
                message=transcription,
            )
            chat_response = await chat_service.chat(chat_request)
            
            audio_data = await voice_service.text_to_speech(chat_response.response.content)
            
            return StreamingResponse(
                iter([audio_data]),
                media_type="audio/wav",
                headers={
                    "X-Transcription": transcription,
                    "X-Response-Text": chat_response.response.content,
                    "X-Conversation-Id": str(chat_response.conversation_id),
                }
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.post(
        "/voice/speak",
        summary="Convert text to speech",
        description="""
        Generate audio from text using text-to-speech synthesis.
        
        **Returns:** WAV audio file
        """,
        responses={
            200: {
                "description": "Audio file generated",
                "content": {"audio/wav": {}}
            },
            500: {"description": "Server error"},
        },
        tags=["Voice"],
    )
    async def text_to_speech(text: str):
        """Convert text to speech audio."""
        try:
            voice_service = get_voice_service()
            audio_data = await voice_service.text_to_speech(text)
            
            return StreamingResponse(
                iter([audio_data]),
                media_type="audio/wav"
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return router
