from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional


class ILLMProvider(ABC):
    @abstractmethod
    async def generate(
        self, prompt: str, system_prompt: Optional[str] = None, **kwargs: Any
    ) -> str:
        pass

    @abstractmethod
    async def generate_stream(
        self, prompt: str, system_prompt: Optional[str] = None, **kwargs: Any
    ) -> AsyncIterator[str]:
        pass


class IVectorStore(ABC):
    @abstractmethod
    async def add_documents(
        self, documents: List[str], metadatas: List[Dict[str, Any]], ids: List[str]
    ) -> None:
        pass

    @abstractmethod
    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def delete_collection(self, collection_name: str) -> None:
        pass


class IRepository(ABC):
    @abstractmethod
    async def find_by_id(self, id: int) -> Optional[Any]:
        pass

    @abstractmethod
    async def find_all(self) -> List[Any]:
        pass

    @abstractmethod
    async def save(self, entity: Any) -> Any:
        pass

    @abstractmethod
    async def delete(self, id: int) -> bool:
        pass


class IDocumentProcessor(ABC):
    @abstractmethod
    async def process_file(self, file_path: str, file_type: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        pass
