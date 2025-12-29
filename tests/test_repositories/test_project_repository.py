"""
Tests for ProjectRepository

Tests CRUD operations and business logic for Project entities.
"""

import pytest
from sqlalchemy.orm import Session

from src.models.database import Project
from src.repositories.project_repository import ProjectRepository


@pytest.mark.unit
class TestProjectRepository:
    """Test suite for ProjectRepository"""
    
    def test_create_project(self, project_repo: ProjectRepository, test_user):
        """Test creating a new project"""
        project = Project(
            user_id=test_user.id,
            name="New Project",
            description="Test description",
            color="#ff0000",
            agent_name="Agent",
            system_prompt="Prompt",
            tools=["calculator"],
        )
        
        created = project_repo.create(project)
        
        assert created.id is not None
        assert created.name == "New Project"
        assert created.user_id == test_user.id
        assert created.color == "#ff0000"
        assert created.tools == ["calculator"]
        assert created.created_at is not None
        assert created.updated_at is not None
    
    def test_find_by_id_existing(self, project_repo: ProjectRepository, test_project):
        """Test finding an existing project by ID"""
        found = project_repo.find_by_id(test_project.id)
        
        assert found is not None
        assert found.id == test_project.id
        assert found.name == test_project.name
    
    def test_find_by_id_nonexistent(self, project_repo: ProjectRepository):
        """Test finding a non-existent project returns None"""
        found = project_repo.find_by_id(99999)
        
        assert found is None
    
    def test_find_by_user(self, project_repo: ProjectRepository, test_db: Session, test_user, project_factory):
        """Test finding all projects for a user"""
        # Create multiple projects
        project_factory.create(test_db, test_user.id, name="Project 1")
        project_factory.create(test_db, test_user.id, name="Project 2")
        project_factory.create(test_db, test_user.id, name="Project 3")
        
        projects = project_repo.find_by_user(test_user.id)
        
        assert len(projects) >= 3
        assert all(p.user_id == test_user.id for p in projects)
        # Should be ordered by updated_at DESC
        assert projects[0].updated_at >= projects[-1].updated_at
    
    def test_find_all(self, project_repo: ProjectRepository, test_db: Session, test_user, project_factory):
        """Test finding all projects"""
        initial_count = len(project_repo.find_all())
        
        # Create test projects
        project_factory.create(test_db, test_user.id, name="Project A")
        project_factory.create(test_db, test_user.id, name="Project B")
        
        all_projects = project_repo.find_all()
        
        assert len(all_projects) == initial_count + 2
    
    def test_update_project(self, project_repo: ProjectRepository, test_project):
        """Test updating a project"""
        test_project.name = "Updated Name"
        test_project.description = "Updated description"
        
        updated = project_repo.update(test_project)
        
        assert updated.name == "Updated Name"
        assert updated.description == "Updated description"
        # updated_at should be refreshed
        assert updated.updated_at is not None
    
    def test_delete_project(self, project_repo: ProjectRepository, test_db: Session, test_user):
        """Test deleting a project"""
        # Create a project to delete
        project = Project(
            user_id=test_user.id,
            name="To Delete",
            description="Will be deleted",
        )
        created = project_repo.create(project)
        project_id = created.id
        
        # Delete it
        result = project_repo.delete(project_id)
        
        assert result is True
        # Verify it's gone
        found = project_repo.find_by_id(project_id)
        assert found is None
    
    def test_delete_nonexistent_project(self, project_repo: ProjectRepository):
        """Test deleting a non-existent project returns False"""
        result = project_repo.delete(99999)
        
        assert result is False
    
    def test_project_cascade_delete_conversations(self, project_repo: ProjectRepository, test_db: Session, test_project, conversation_factory):
        """Test that deleting a project cascades to conversations"""
        # Create conversations
        conversation_factory.create(test_db, test_project.id, title="Conv 1")
        conversation_factory.create(test_db, test_project.id, title="Conv 2")
        
        # Delete project
        project_repo.delete(test_project.id)
        
        # Verify conversations are also deleted (cascade)
        from src.models.database import Conversation
        remaining_convs = test_db.query(Conversation).filter(
            Conversation.project_id == test_project.id
        ).all()
        
        assert len(remaining_convs) == 0
    
    def test_create_project_with_null_optional_fields(self, project_repo: ProjectRepository, test_user):
        """Test creating a project with minimal required fields"""
        project = Project(
            user_id=test_user.id,
            name="Minimal Project",
            # description, color, etc. are optional
        )
        
        created = project_repo.create(project)
        
        assert created.id is not None
        assert created.name == "Minimal Project"
        assert created.description is None or created.description == ""
