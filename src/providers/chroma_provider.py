from typing import Any, Dict, List, Optional

import chromadb
from langchain_chroma import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.documents import Document

from src.config import settings
from src.core.constants import RAG_TOP_K_DOCUMENTS
from src.core.exceptions import VectorStoreError
from src.core.interfaces import IVectorStore


class ChromaProvider(IVectorStore):
    def __init__(self, collection_name: str = "studybuddy_documents"):
        try:
            self.client = chromadb.HttpClient(
                host=settings.CHROMA_HOST,
                port=settings.CHROMA_PORT,
            )
            
            self.embeddings = OllamaEmbeddings(
                model=settings.OLLAMA_MODEL,
                base_url="http://ollama:11434"
            )
            
            self.vectorstore = Chroma(
                client=self.client,
                collection_name=collection_name,
                embedding_function=self.embeddings,
            )
            
        except Exception as e:
            raise VectorStoreError(f"Failed to initialize ChromaDB: {str(e)}")

    async def add_documents(
        self, documents: List[str], metadatas: List[Dict[str, Any]], ids: List[str]
    ) -> None:
        try:
            docs = [
                Document(page_content=doc, metadata=meta)
                for doc, meta in zip(documents, metadatas)
            ]
            
            self.vectorstore.add_documents(documents=docs, ids=ids)
        except Exception as e:
            raise VectorStoreError(f"Failed to add documents: {str(e)}")

    async def search(self, query: str, top_k: int = 5, filter: Optional[Dict] = None) -> List[Dict[str, Any]]:
        try:
            results = self.vectorstore.similarity_search_with_score(
                query=query,
                k=top_k,
                filter=filter
            )
            
            formatted_results = []
            for doc, score in results:
                result = {
                    'document': doc.page_content,
                    'metadata': doc.metadata,
                    'score': score,
                    'id': doc.metadata.get('id', None)
                }
                formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            raise VectorStoreError(f"Failed to search documents: {str(e)}")

    def as_retriever(self, search_type: str = "similarity", search_kwargs: Optional[Dict] = None):
        return self.vectorstore.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs or {"k": 5}
        )

    async def delete_collection(self, collection_name: str) -> None:
        try:
            self.client.delete_collection(name=collection_name)
        except Exception as e:
            raise VectorStoreError(f"Failed to delete collection: {str(e)}")
