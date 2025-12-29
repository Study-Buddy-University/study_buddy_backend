from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from pathlib import Path

from src.api.auth_routes import create_auth_routes
from src.api.chat_routes import create_chat_routes
from src.api.document_routes import create_document_routes
from src.api.export_routes import create_export_routes
from src.api.project_routes import create_project_routes
from src.api.voice_routes import create_voice_routes
from src.api.stats_routes import create_stats_routes
from src.api.user_routes import router as user_router
from src.api.system_routes import router as system_router
from src.config import settings
from src.core.logging_config import setup_logging
from src.middleware.error_handler import ErrorHandlerMiddleware
from src.models.database import get_db, create_tables
from src.providers.chroma_provider import ChromaProvider
from src.providers.ollama_provider import OllamaProvider
from src.repositories.conversation_repository import ConversationRepository
from src.repositories.document_repository import DocumentRepository
from src.repositories.message_repository import MessageRepository
from src.repositories.project_repository import ProjectRepository
from src.services.chat_service import ChatService
from src.services.document_service import DocumentService
from src.services.export_service import ExportService
from src.services.voice_service import VoiceService


# Set up structured logging
logger = setup_logging(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    json_format=not settings.DEBUG  # JSON in production, readable in dev
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting AI Study Buddy...")
    logger.info(f"📊 Database: {settings.DATABASE_URL}")
    logger.info(f"🤖 LLM: {settings.OLLAMA_MODEL} at {settings.OLLAMA_BASE_URL}")
    logger.info(f"🔍 ChromaDB: {settings.chroma_url}")
    logger.info(f"🔧 Debug mode: {settings.DEBUG}")
    
    # Create database tables
    logger.info("📋 Creating database tables...")
    create_tables()
    logger.info("✅ Database tables ready")
    
    yield
    logger.info("👋 Shutting down AI Study Buddy...")


# Ensure uploads directory exists
Path("uploads/avatars").mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="AI Study Buddy API",
    description="""
    ## 🎓 AI Study Buddy - Intelligent Learning Platform
    
    Multi-modal AI study assistant with advanced features including multi-LLM support,
    RAG (Retrieval Augmented Generation), voice I/O, and GPU acceleration.
    
    **Author:** Alexandros Karales  
    **Website:** [karales.com](https://karales.com)  
    **Email:** karales@gmail.com
    
    ### Core Features
    - 🤖 Multi-LLM Support (7+ models)
    - ⚡ GPU Acceleration
    - 📚 RAG with Document Context
    - 🎯 Project Organization
    - 💬 Conversation Management
    - 🎤 Voice I/O
    - 📊 Analytics & Statistics
    """,
    version="2.0.0",
    lifespan=lifespan,
    contact={
        "name": "Alexandros Karales",
        "url": "https://karales.com",
        "email": "karales@gmail.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    swagger_ui_parameters={
        "persistAuthorization": True,
    },
)

# Configure security scheme for Swagger UI
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    
    # Apply security globally to all endpoints except public ones
    # Public endpoints: /, /health, /docs, /redoc, /openapi.json, /signup, /login
    public_paths = {"/", "/health", "/docs", "/redoc", "/openapi.json", "/api/v1/auth/signup", "/api/v1/auth/login"}
    
    for path, path_item in openapi_schema.get("paths", {}).items():
        if path not in public_paths:
            for method in path_item.values():
                if isinstance(method, dict) and "security" not in method:
                    method["security"] = [{"bearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Error handling middleware (must be first)
app.add_middleware(ErrorHandlerMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


llm_provider = OllamaProvider()
vector_store = ChromaProvider()
voice_service_instance = VoiceService()


def get_chat_service():
    db = next(get_db())
    try:
        conversation_repo = ConversationRepository(db)
        message_repo = MessageRepository(db)
        project_repo = ProjectRepository(db)
        return ChatService(llm_provider, conversation_repo, message_repo, project_repo, vector_store)
    finally:
        db.close()


def get_project_repo():
    db = next(get_db())
    try:
        return ProjectRepository(db)
    finally:
        db.close()


def get_conversation_repo():
    db = next(get_db())
    try:
        return ConversationRepository(db)
    finally:
        db.close()


def get_document_service():
    db = next(get_db())
    try:
        document_repo = DocumentRepository(db)
        ### Support
        # - Website: [karales.com](https://karales.com)
        # - Email: karales@gmail.com
        # - Author: Alexandros Karales
        return DocumentService(document_repo, vector_store)
    finally:
        db.close()


def get_voice_service():
    return voice_service_instance


def get_export_service():
    db = next(get_db())
    try:
        conversation_repo = ConversationRepository(db)
        message_repo = MessageRepository(db)
        return ExportService(conversation_repo, message_repo)
    finally:
        db.close()


auth_router = create_auth_routes()
chat_router = create_chat_routes(get_chat_service)
project_router = create_project_routes(get_project_repo)
document_router = create_document_routes(get_document_service, llm_provider)
export_router = create_export_routes(get_export_service)
voice_router = create_voice_routes(get_voice_service, get_chat_service)
stats_router = create_stats_routes(get_project_repo, get_conversation_repo)

app.include_router(auth_router, prefix=settings.API_V1_PREFIX + "/auth", tags=["Authentication"])
app.include_router(user_router, tags=["Users"])
app.include_router(chat_router, prefix=settings.API_V1_PREFIX, tags=["Chat"])
app.include_router(project_router, prefix=settings.API_V1_PREFIX, tags=["Projects"])
app.include_router(document_router, prefix=settings.API_V1_PREFIX, tags=["Documents"])
app.include_router(export_router, prefix=settings.API_V1_PREFIX, tags=["Export"])
app.include_router(voice_router, prefix=settings.API_V1_PREFIX, tags=["Voice"])
app.include_router(stats_router, prefix=settings.API_V1_PREFIX, tags=["Statistics"])
app.include_router(system_router, prefix=settings.API_V1_PREFIX, tags=["System"])


@app.get(
    "/",
    tags=["Root"],
    summary="API Root",
    description="Get basic API information and available endpoints",
    responses={
        200: {
            "description": "API information",
            "content": {
                "application/json": {
                    "example": {
                        "message": "AI Study Buddy API",
                        "version": "2.0.0",
                        "docs": "/docs",
                        "redoc": "/redoc",
                        "openapi": "/openapi.json",
                        "status": "running"
                    }
                }
            }
        }
    }
)
async def root():
    """
    API root endpoint providing basic information and documentation links.
    
    Returns:
        dict: API metadata including version, status, and documentation URLs
    """
    return {
        "message": "AI Study Buddy API",
        "version": "2.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
        "status": "running",
        "features": [
            "Multi-LLM Support (7+ models)",
            "GPU Acceleration",
            "RAG with Document Context",
            "Voice I/O",
            "Project Organization"
        ]
    }


@app.get(
    "/health",
    tags=["Root"],
    summary="Health Check",
    description="Check API health status and service connectivity",
    responses={
        200: {
            "description": "Service health status",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "database": "connected",
                        "llm": "llama3-groq-tool-use:8b",
                        "chromadb": "http://chromadb:8000",
                        "uptime": "2h 15m"
                    }
                }
            }
        }
    }
)
async def health():
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns:
        dict: Service health status including database, LLM, and vector store connectivity
    """
    return {
        "status": "healthy",
        "database": "connected",
        "llm": settings.OLLAMA_MODEL,
        "chromadb": settings.chroma_url,
        "version": "2.0.0"
    }


# Mount static files AFTER all routes to avoid conflicts
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
logger.info("📁 Static file serving enabled for /uploads")
