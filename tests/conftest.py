"""
Pytest configuration and fixtures for AI Study Buddy tests

This module provides reusable fixtures for testing including:
- Database setup/teardown
- Mock providers (LLM, vector store)
- Test data factories
- Authentication helpers
"""

import pytest
from datetime import datetime
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.models.database import Base, User, Project, Conversation, Message, Document
from src.repositories.project_repository import ProjectRepository
from src.repositories.conversation_repository import ConversationRepository
from src.repositories.message_repository import MessageRepository
from src.repositories.document_repository import DocumentRepository


@pytest.fixture(scope="session")
def test_engine():
    """Create an in-memory SQLite engine for testing"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def test_db(test_engine) -> Generator[Session, None, None]:
    """Create a new database session for each test"""
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestSessionLocal()
    
    try:
        yield session
    finally:
        # Clean up all data after test
        session.query(Message).delete()
        session.query(Conversation).delete()
        session.query(Document).delete()
        session.query(Project).delete()
        session.query(User).delete()
        session.commit()
        session.close()


@pytest.fixture
def test_user(test_db: Session) -> User:
    """Create a test user"""
    user = User(
        email="test@example.com",
        name="Test User",
        password_hash="$argon2id$v=19$m=65536,t=3,p=4$test",  # Placeholder hash
    )
    test_db.add(user)
    test_db.commit()  # Commit so it's visible across sessions
    test_db.refresh(user)
    return user


@pytest.fixture
def test_project(test_db: Session, test_user: User) -> Project:
    """Create a test project"""
    project = Project(
        user_id=test_user.id,
        name="Test Project",
        description="A test project for unit testing",
        color="#3b82f6",
        agent_name="Test Agent",
        system_prompt="You are a helpful test assistant.",
        tools=["calculator", "web_search"],
    )
    test_db.add(project)
    test_db.commit()
    test_db.refresh(project)
    return project


@pytest.fixture
def test_conversation(test_db: Session, test_project: Project) -> Conversation:
    """Create a test conversation"""
    conversation = Conversation(
        project_id=test_project.id,
        title="Test Conversation",
        total_tokens=0,
    )
    test_db.add(conversation)
    test_db.commit()
    test_db.refresh(conversation)
    return conversation


@pytest.fixture
def test_message(test_db: Session, test_conversation: Conversation) -> Message:
    """Create a test message"""
    message = Message(
        conversation_id=test_conversation.id,
        role="user",
        content="Test message content",
        message_type="text",
    )
    test_db.add(message)
    test_db.commit()
    test_db.refresh(message)
    return message


@pytest.fixture
def test_document(test_db: Session, test_project: Project) -> Document:
    """Create a test document"""
    document = Document(
        project_id=test_project.id,
        filename="test_document.pdf",
        file_type="application/pdf",
        file_path="/tmp/test_document.pdf",
        file_size=1024,
        summary="A test document for unit testing",
    )
    test_db.add(document)
    test_db.commit()
    test_db.refresh(document)
    return document


# Repository fixtures
@pytest.fixture
def project_repo(test_db: Session) -> ProjectRepository:
    """Create a ProjectRepository instance"""
    return ProjectRepository(test_db)


@pytest.fixture
def conversation_repo(test_db: Session) -> ConversationRepository:
    """Create a ConversationRepository instance"""
    return ConversationRepository(test_db)


@pytest.fixture
def message_repo(test_db: Session) -> MessageRepository:
    """Create a MessageRepository instance"""
    return MessageRepository(test_db)


@pytest.fixture
def document_repo(test_db: Session) -> DocumentRepository:
    """Create a DocumentRepository instance"""
    return DocumentRepository(test_db)


# Mock provider fixtures
@pytest.fixture
def mock_llm_provider(mocker):
    """Mock LLM provider for testing"""
    from unittest.mock import AsyncMock
    
    mock = mocker.MagicMock()
    # Use AsyncMock for async methods
    mock.generate = AsyncMock(return_value="Mocked LLM response")
    
    # For async generator, create a mock that returns an async generator
    async def mock_stream_gen(*args, **kwargs):
        for chunk in ["Mocked ", "streamed ", "response"]:
            yield chunk
    mock.generate_stream = mocker.MagicMock(return_value=mock_stream_gen())
    
    return mock


@pytest.fixture
def mock_vector_store(mocker):
    """Mock vector store for testing"""
    mock = mocker.MagicMock()
    mock.add_document.return_value = "doc_id_123"
    mock.similarity_search.return_value = [
        {"content": "Relevant content 1", "score": 0.9},
        {"content": "Relevant content 2", "score": 0.8},
    ]
    mock.delete_document.return_value = True
    return mock


# Data factory helpers
class ProjectFactory:
    """Factory for creating test projects"""
    
    @staticmethod
    def create(
        db: Session,
        user_id: int,
        name: str = "Test Project",
        **kwargs
    ) -> Project:
        """Create a project with default or custom values"""
        defaults = {
            "description": "Test description",
            "color": "#3b82f6",
            "agent_name": "Test Agent",
            "system_prompt": "Test prompt",
            "tools": ["calculator"],
        }
        defaults.update(kwargs)
        
        project = Project(user_id=user_id, name=name, **defaults)
        db.add(project)
        db.commit()
        db.refresh(project)
        return project


class ConversationFactory:
    """Factory for creating test conversations"""
    
    @staticmethod
    def create(
        db: Session,
        project_id: int,
        title: str = "Test Conversation",
        **kwargs
    ) -> Conversation:
        """Create a conversation with default or custom values"""
        defaults = {
            "total_tokens": 0,
        }
        defaults.update(kwargs)
        
        conversation = Conversation(project_id=project_id, title=title, **defaults)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation


@pytest.fixture
def project_factory() -> type[ProjectFactory]:
    """Provide ProjectFactory for tests"""
    return ProjectFactory


@pytest.fixture
def conversation_factory() -> type[ConversationFactory]:
    """Provide ConversationFactory for tests"""
    return ConversationFactory
