import os
from pathlib import Path
from typing import BinaryIO, List

from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import settings
from src.core.constants import RAG_TOP_K_DOCUMENTS
from src.core.exceptions import DocumentProcessingError
from src.core.interfaces import IVectorStore
from src.models.database import Document
from src.repositories.document_repository import DocumentRepository


class DocumentService:
    def __init__(self, document_repo: DocumentRepository, vector_store: IVectorStore):
        self.document_repo = document_repo
        self.vector_store = vector_store
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def upload_document(
        self, project_id: int, file: BinaryIO, filename: str, file_type: str
    ) -> Document:
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"Starting document upload: {filename} for project {project_id}")
            
            file_path = self.upload_dir / f"{project_id}_{filename}"
            
            with open(file_path, "wb") as f:
                content = file.read()
                f.write(content)
            
            file_size = len(content)
            logger.info(f"File saved: {file_path} ({file_size} bytes)")
            
            document = Document(
                project_id=project_id,
                filename=filename,
                file_type=file_type,
                file_path=str(file_path),
                file_size=file_size,
            )
            
            created_doc = self.document_repo.create(document)
            logger.info(f"Document record created with ID: {created_doc.id}")
            
            # Index document - this should show logs
            try:
                await self._process_and_index_document(created_doc, content)
                logger.info(f"✅ Document indexing completed for: {filename}")
            except Exception as index_error:
                logger.error(f"❌ Indexing failed for {filename}: {str(index_error)}", exc_info=True)
                # Don't fail upload if indexing fails, but log it
            
            return created_doc
            
        except Exception as e:
            logger.error(f"Failed to upload document {filename}: {str(e)}", exc_info=True)
            raise DocumentProcessingError(f"Failed to upload document: {str(e)}")

    async def _process_and_index_document(self, document: Document, content: bytes):
        try:
            from src.utils.document_processor import extract_text
            import logging
            
            logger = logging.getLogger(__name__)
            logger.info(f"Starting indexing for document {document.id}: {document.filename}")
            
            text = extract_text(content, document.file_type, document.filename)
            logger.info(f"Extracted {len(text)} characters from {document.filename}")
            
            chunks = self._chunk_text(text)
            logger.info(f"Created {len(chunks)} chunks from {document.filename}")
            
            if not chunks:
                logger.warning(f"No chunks created for {document.filename}")
                return
            
            ids = [f"{document.id}_chunk_{i}" for i in range(len(chunks))]
            metadatas = [
                {
                    "document_id": document.id,
                    "filename": document.filename,
                    "chunk_index": i,
                    "project_id": document.project_id,
                }
                for i in range(len(chunks))
            ]
            
            logger.info(f"Adding {len(chunks)} chunks to vector store for {document.filename}")
            await self.vector_store.add_documents(
                documents=chunks, metadatas=metadatas, ids=ids
            )
            logger.info(f"Successfully indexed {document.filename} to vector store")
            
        except Exception as e:
            import logging
            logging.error(f"Failed to index document {document.filename}: {str(e)}", exc_info=True)
            raise DocumentProcessingError(f"Failed to index document: {str(e)}")

    def _chunk_text(self, text: str) -> List[str]:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
            is_separator_regex=False,
        )
        
        chunks = text_splitter.split_text(text)
        return chunks

    async def search_documents(self, project_id: int, query: str, top_k: int = RAG_TOP_K_DOCUMENTS) -> List[dict]:
        try:
            results = await self.vector_store.search(query, top_k=top_k)
            
            filtered_results = [
                r for r in results if r.get("metadata", {}).get("project_id") == project_id
            ]
            
            return filtered_results
            
        except Exception as e:
            raise DocumentProcessingError(f"Failed to search documents: {str(e)}")

    def get_project_documents(self, project_id: int) -> List[Document]:
        return self.document_repo.find_by_project(project_id)
    
    def get_document_by_id(self, document_id: int) -> Document:
        """Get a document by its ID."""
        return self.document_repo.find_by_id(document_id)

    async def summarize_document(self, document_id: int, llm_provider) -> str:
        try:
            document = self.document_repo.find_by_id(document_id)
            if not document:
                raise DocumentProcessingError("Document not found")
            
            with open(document.file_path, 'rb') as f:
                content = f.read()
            
            from src.utils.document_processor import extract_text
            text = extract_text(content, document.file_type, document.filename)
            
            prompt = f"""Please provide a concise summary of the following document:

{text[:3000]}

Summary:"""
            
            summary = await llm_provider.generate(prompt)
            
            document.summary = summary
            self.document_repo.update(document)
            
            return summary
            
        except Exception as e:
            raise DocumentProcessingError(f"Failed to summarize document: {str(e)}")

    def delete_document(self, document_id: int) -> bool:
        document = self.document_repo.find_by_id(document_id)
        if document and os.path.exists(document.file_path):
            os.remove(document.file_path)
        return self.document_repo.delete(document_id)
