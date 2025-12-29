"""Tests for project API routes"""

import pytest
from fastapi.testclient import TestClient
from src.app import app
from src.models.database import get_db


@pytest.fixture
def client(test_db, test_engine):
    """Create a test client with test database"""
    from sqlalchemy.orm import sessionmaker
    
    # Use the same engine for both test and app
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.mark.integration
class TestProjectRoutes:
    """Test suite for project API endpoints"""
    
    # TODO: Fix database session isolation issue
    # def test_list_projects_success(self, client, test_project):
    #     """Test GET /projects returns project list"""
    #     response = client.get("/api/v1/projects")
    #     
    #     assert response.status_code == 200
    #     data = response.json()
    #     assert isinstance(data, list)
    #     assert len(data) > 0
    #     assert any(p["id"] == test_project.id for p in data)
    
    # TODO: Fix database session isolation issue
    # def test_get_project_success(self, client, test_project):
    #     """Test GET /projects/{id} returns specific project"""
    #     response = client.get(f"/api/v1/projects/{test_project.id}")
    #     
    #     assert response.status_code == 200
    #     data = response.json()
    #     assert data["id"] == test_project.id
    #     assert data["name"] == test_project.name
    
    def test_get_project_not_found(self, client):
        """Test GET /projects/{id} with non-existent ID returns 404"""
        response = client.get("/api/v1/projects/99999")
        
        assert response.status_code == 404
    
    def test_create_project_success(self, client):
        """Test POST /projects creates new project"""
        project_data = {
            "name": "New API Project",
            "description": "Created via API",
            "color": "#ff0000",
            "agent_name": "Test Agent",
            "system_prompt": "Test prompt",
            "tools": ["calculator"]
        }
        
        response = client.post("/api/v1/projects", json=project_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New API Project"
        assert data["id"] is not None
    
    # TODO: Fix database session isolation issue
    # def test_update_project_success(self, client, test_project):
    #     """Test PUT /projects/{id} updates project"""
    #     update_data = {
    #         "name": "Updated Name",
    #         "description": test_project.description,
    #     }
    #     
    #     response = client.put(f"/api/v1/projects/{test_project.id}", json=update_data)
    #     
    #     assert response.status_code == 200
    #     data = response.json()
    #     assert data["name"] == "Updated Name"
    
    # TODO: Fix database session isolation issue
    # def test_delete_project_success(self, client, test_db, test_user):
    #     """Test DELETE /projects/{id} deletes project"""
    #     # Create a project to delete
    #     from src.models.database import Project
    #     project = Project(user_id=test_user.id, name="To Delete")
    #     test_db.add(project)
    #     test_db.commit()
    #     project_id = project.id
    #     
    #     response = client.delete(f"/api/v1/projects/{project_id}")
    #     
    #     assert response.status_code == 204
    #     
    #     # Verify it's deleted
    #     get_response = client.get(f"/api/v1/projects/{project_id}")
    #     assert get_response.status_code == 404
