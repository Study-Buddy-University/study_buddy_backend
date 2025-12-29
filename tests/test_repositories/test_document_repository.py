"""Tests for DocumentRepository"""

import pytest
from src.models.database import Document
from src.repositories.document_repository import DocumentRepository


@pytest.mark.unit
class TestDocumentRepository:
    """Test suite for DocumentRepository"""
    
    def test_create_document(self, document_repo: DocumentRepository, test_project):
        """Test creating a new document"""
        document = Document(
            project_id=test_project.id,
            filename="test.pdf",
            file_type="application/pdf",
            file_path="/tmp/test.pdf",
            file_size=1024,
            summary="Test document"
        )
        
        created = document_repo.create(document)
        
        assert created.id is not None
        assert created.filename == "test.pdf"
        assert created.project_id == test_project.id
        assert created.file_size == 1024
        assert created.created_at is not None
    
    def test_find_by_id(self, document_repo: DocumentRepository, test_document):
        """Test finding document by ID"""
        found = document_repo.find_by_id(test_document.id)
        
        assert found is not None
        assert found.id == test_document.id
        assert found.filename == test_document.filename
    
    def test_find_by_project(self, document_repo: DocumentRepository, test_db, test_project):
        """Test finding all documents for a project"""
        # Create multiple documents
        for i in range(3):
            doc = Document(
                project_id=test_project.id,
                filename=f"doc{i}.pdf",
                file_type="application/pdf",
                file_path=f"/tmp/doc{i}.pdf",
                file_size=1024 * (i + 1)
            )
            test_db.add(doc)
        test_db.commit()
        
        documents = document_repo.find_by_project(test_project.id)
        
        assert len(documents) >= 3
        assert all(d.project_id == test_project.id for d in documents)
    
    def test_update_document(self, document_repo: DocumentRepository, test_document):
        """Test updating a document"""
        test_document.summary = "Updated summary"
        test_document.file_size = 2048
        
        updated = document_repo.update(test_document)
        
        assert updated.summary == "Updated summary"
        assert updated.file_size == 2048
    
    def test_delete_document(self, document_repo: DocumentRepository, test_db, test_project):
        """Test deleting a document"""
        document = Document(
            project_id=test_project.id,
            filename="to_delete.pdf",
            file_type="application/pdf",
            file_path="/tmp/to_delete.pdf"
        )
        created = document_repo.create(document)
        
        result = document_repo.delete(created.id)
        
        assert result is True
        assert document_repo.find_by_id(created.id) is None
    
    def test_document_with_null_optional_fields(self, document_repo: DocumentRepository, test_project):
        """Test creating document with minimal required fields"""
        document = Document(
            project_id=test_project.id,
            filename="minimal.txt",
            file_type="text/plain",
            file_path="/tmp/minimal.txt"
            # file_size and summary are optional
        )
        
        created = document_repo.create(document)
        
        assert created.id is not None
        assert created.filename == "minimal.txt"
        assert created.file_size is None
        assert created.summary is None
    
    def test_find_by_project_empty(self, document_repo: DocumentRepository, test_db, test_user):
        """Test finding documents for project with no documents"""
        from src.models.database import Project
        
        empty_project = Project(
            user_id=test_user.id,
            name="Empty Project"
        )
        test_db.add(empty_project)
        test_db.commit()
        
        documents = document_repo.find_by_project(empty_project.id)
        
        assert len(documents) == 0
