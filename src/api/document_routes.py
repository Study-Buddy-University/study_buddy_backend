from typing import Callable, List
import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, Body
from fastapi.responses import FileResponse, PlainTextResponse
import os

from src.models.schemas import DocumentResponse, DocumentSearchRequest, DocumentSearchResponse
from src.providers.ollama_provider import OllamaProvider
from src.services.document_service import DocumentService

logger = logging.getLogger(__name__)


def create_document_routes(get_service: Callable[[], DocumentService], llm_provider: OllamaProvider) -> APIRouter:
    router = APIRouter()

    @router.post(
        "/documents/upload",
        response_model=DocumentResponse,
        status_code=201,
        summary="Upload a document",
        description="""
        Upload a document to a project for RAG (Retrieval Augmented Generation).
        
        **Supported formats:** PDF, TXT, MD, DOCX
        
        **Process:** File saved → Text extracted → Chunked → Embedded → Stored in vector DB
        """,
        responses={
            201: {"description": "Document uploaded successfully"},
            400: {"description": "Invalid file"},
            500: {"description": "Server error"},
        },
        tags=["Documents"],
    )
    async def upload_document(
        project_id: int = Form(...),
        file: UploadFile = File(...),
        service: DocumentService = Depends(get_service),
    ):
        """Upload and process a document for RAG."""
        try:
            logger.info(f"Uploading document '{file.filename}' to project {project_id}")
            
            if not file.filename:
                raise HTTPException(status_code=400, detail="Filename is required")
            
            content_type = file.content_type or "application/octet-stream"
            
            document = await service.upload_document(
                project_id=project_id,
                file=file.file,
                filename=file.filename,
                file_type=content_type,
            )
            
            logger.info(f"Successfully uploaded document {document.id}")
            return DocumentResponse.model_validate(document)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to upload document: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to upload document")

    @router.get(
        "/documents/project/{project_id}",
        response_model=List[DocumentResponse],
        summary="Get all documents for a project",
        description="Retrieve all documents uploaded to a specific project.",
        responses={
            200: {"description": "List of documents"},
            500: {"description": "Server error"},
        },
        tags=["Documents"],
    )
    async def get_project_documents(
        project_id: int,
        service: DocumentService = Depends(get_service),
    ):
        """Get all documents for a project."""
        try:
            logger.info(f"Fetching documents for project {project_id}")
            documents = service.get_project_documents(project_id)
            logger.info(f"Found {len(documents)} documents for project {project_id}")
            return [DocumentResponse.model_validate(doc) for doc in documents]
        except Exception as e:
            logger.error(f"Failed to fetch documents for project {project_id}: {e}", exc_info=True)
            return []

    @router.post(
        "/documents/search",
        response_model=DocumentSearchResponse,
        summary="Semantic search documents",
        description="Search documents using vector similarity with relevance scores.",
        responses={
            200: {"description": "Search results"},
            500: {"description": "Server error"},
        },
        tags=["Documents"],
    )
    async def search_documents(
        request: DocumentSearchRequest,
        service: DocumentService = Depends(get_service),
    ):
        """Semantic search across project documents."""
        try:
            results = await service.search_documents(
                project_id=request.project_id,
                query=request.query,
                top_k=request.top_k,
            )
            return DocumentSearchResponse(results=results)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.post(
        "/documents/{document_id}/summarize",
        summary="Generate document summary",
        description="Use LLM to generate a concise summary.",
        responses={
            200: {"description": "Summary generated"},
            500: {"description": "Server error"},
        },
        tags=["Documents"],
    )
    async def summarize_document(
        document_id: int,
        service: DocumentService = Depends(get_service),
    ):
        """Generate AI summary of a document."""
        try:
            summary = await service.summarize_document(document_id, llm_provider)
            return {"document_id": document_id, "summary": summary}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get(
        "/documents/{document_id}",
        response_model=DocumentResponse,
        summary="Get document by ID",
        description="Retrieve a single document's metadata by ID.",
        responses={
            200: {"description": "Document found"},
            404: {"description": "Not found"},
            500: {"description": "Server error"},
        },
        tags=["Documents"],
    )
    async def get_document(
        document_id: int,
        service: DocumentService = Depends(get_service),
    ):
        """Get document metadata by ID."""
        try:
            document = service.get_document_by_id(document_id)
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")
            return DocumentResponse.model_validate(document)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to fetch document {document_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @router.get(
        "/documents/{document_id}/content",
        summary="Get document content",
        description="Retrieve the raw text content of a document.",
        responses={
            200: {"description": "Document content"},
            404: {"description": "Not found"},
            500: {"description": "Server error"},
        },
        tags=["Documents"],
    )
    async def get_document_content(
        document_id: int,
        service: DocumentService = Depends(get_service),
    ):
        """Get document text content.
        
        Supports:
        - PDF files (.pdf)
        - Markdown files (.md, .markdown)
        - Text files (.txt)
        - Code files (.py, .js, .ts, .cpp, .c, .java, .go, etc.)
        - DOCX files (.docx)
        """
        try:
            logger.info(f"📄 Fetching content for document {document_id}")
            
            document = service.get_document_by_id(document_id)
            if not document:
                logger.warning(f"❌ Document {document_id} not found in database")
                raise HTTPException(status_code=404, detail="Document not found")
            
            logger.info(f"📁 Document: {document.filename} (type: {document.file_type}, path: {document.file_path})")
            
            # Check if file exists
            if not os.path.exists(document.file_path):
                logger.error(f"❌ File not found on disk: {document.file_path}")
                raise HTTPException(status_code=404, detail="Document file not found on server")
            
            # Get file size for logging
            file_size = os.path.getsize(document.file_path)
            logger.info(f"📊 File size: {file_size} bytes ({file_size / 1024:.2f} KB)")
            
            # Read file as bytes
            with open(document.file_path, 'rb') as f:
                content_bytes = f.read()
            
            # Extract text using document processor
            from src.utils.document_processor import extract_text
            
            try:
                text_content = extract_text(
                    content=content_bytes,
                    file_type=document.file_type,
                    filename=document.filename
                )
                logger.info(f"✅ Successfully extracted {len(text_content)} characters")
                return PlainTextResponse(content=text_content)
                
            except ValueError as ve:
                # Unsupported file type
                logger.warning(f"⚠️ Unsupported file type for {document.filename}: {ve}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot display this file type as text. {str(ve)}"
                )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"💥 CRITICAL ERROR reading document {document_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to read document content: {str(e)}"
            )

    @router.get(
        "/documents/{document_id}/download",
        summary="Download document",
        description="Download the original document file.",
        responses={
            200: {"description": "Document file"},
            404: {"description": "Not found"},
            500: {"description": "Server error"},
        },
        tags=["Documents"],
    )
    async def download_document(
        document_id: int,
        service: DocumentService = Depends(get_service),
    ):
        """Download document file."""
        try:
            document = service.get_document_by_id(document_id)
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")
            
            if not os.path.exists(document.file_path):
                raise HTTPException(status_code=404, detail="Document file not found")
            
            return FileResponse(
                path=document.file_path,
                filename=document.filename,
                media_type=document.file_type,
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to download document {document_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @router.delete(
        "/documents/{document_id}",
        status_code=204,
        summary="Delete document",
        description="Delete document and its vector embeddings.",
        responses={
            204: {"description": "Document deleted"},
            404: {"description": "Not found"},
            500: {"description": "Server error"},
        },
        tags=["Documents"],
    )
    async def delete_document(
        document_id: int,
        service: DocumentService = Depends(get_service),
    ):
        """Delete document and embeddings."""
        try:
            success = service.delete_document(document_id)
            if not success:
                raise HTTPException(status_code=404, detail="Document not found")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return router
