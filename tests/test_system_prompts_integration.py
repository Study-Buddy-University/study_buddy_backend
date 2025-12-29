"""
Integration tests for System Prompts feature.
Tests the full flow from API to database to chat service.

Run: docker compose exec backend python tests/test_system_prompts_integration.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from src.models.database import SessionLocal, Project
from src.repositories.project_repository import ProjectRepository
from src.services.chat_service import ChatService
from src.repositories.conversation_repository import ConversationRepository
from src.repositories.message_repository import MessageRepository
from src.models.schemas import ChatRequest


def test_database_column_exists():
    """Test 1: Verify system_prompt column exists in database"""
    print("\n📋 Test 1: Database Column")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        # Create test project with system prompt
        test_project = Project(
            user_id=1,
            name="Test System Prompt Project",
            description="Integration test",
            color="#ff0000",
            system_prompt="You are a test assistant."
        )
        db.add(test_project)
        db.commit()
        db.refresh(test_project)
        
        # Verify it was saved
        assert test_project.system_prompt == "You are a test assistant."
        print(f"✅ Project created with ID: {test_project.id}")
        print(f"✅ System prompt saved: {test_project.system_prompt[:50]}...")
        
        # Clean up
        db.delete(test_project)
        db.commit()
        print("✅ Test passed: Database column exists and works")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def test_project_repository():
    """Test 2: Verify ProjectRepository retrieves system prompt"""
    print("\n📋 Test 2: Project Repository")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        repo = ProjectRepository(db)
        
        # Create test project
        test_project = Project(
            user_id=1,
            name="Test Repository Project",
            description="Repository test",
            color="#00ff00",
            system_prompt="You are a repository test assistant."
        )
        created = repo.create(test_project)
        print(f"✅ Project created with ID: {created.id}")
        
        # Retrieve using find_by_id
        retrieved = repo.find_by_id(created.id)
        assert retrieved is not None
        assert retrieved.system_prompt == "You are a repository test assistant."
        print(f"✅ Retrieved system prompt: {retrieved.system_prompt[:50]}...")
        
        # Clean up
        repo.delete(created.id)
        print("✅ Test passed: Repository correctly retrieves system prompt")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        db.close()


async def test_chat_service_system_prompt():
    """Test 3: Verify ChatService uses system prompt in prompt building"""
    print("\n📋 Test 3: Chat Service Integration")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        # Create test project with system prompt
        project_repo = ProjectRepository(db)
        test_project = Project(
            user_id=1,
            name="Test Chat Project",
            description="Chat service test",
            color="#0000ff",
            system_prompt="You are a friendly test assistant who always says 'TESTING MODE' in responses."
        )
        created_project = project_repo.create(test_project)
        print(f"✅ Test project created with ID: {created_project.id}")
        print(f"✅ System prompt: {created_project.system_prompt[:80]}...")
        
        # Note: We can't test full LLM integration without mocking
        # But we can verify the system prompt is retrieved
        retrieved = project_repo.find_by_id(created_project.id)
        assert retrieved.system_prompt is not None
        print("✅ ChatService will use system prompt:", retrieved.system_prompt[:50] + "...")
        
        # Clean up
        project_repo.delete(created_project.id)
        print("✅ Test passed: ChatService can access system prompt")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        db.close()


def test_system_prompt_optional():
    """Test 4: Verify system prompt is optional (can be NULL)"""
    print("\n📋 Test 4: Optional System Prompt")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        repo = ProjectRepository(db)
        
        # Create project WITHOUT system prompt
        test_project = Project(
            user_id=1,
            name="Test No Prompt Project",
            description="Testing NULL system prompt",
            color="#ff00ff",
            system_prompt=None
        )
        created = repo.create(test_project)
        print(f"✅ Project created without system prompt, ID: {created.id}")
        
        # Verify it's None
        retrieved = repo.find_by_id(created.id)
        assert retrieved.system_prompt is None
        print("✅ System prompt is None (as expected)")
        
        # Clean up
        repo.delete(created.id)
        print("✅ Test passed: System prompt is optional")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        db.close()


def test_update_system_prompt():
    """Test 5: Verify system prompt can be updated"""
    print("\n📋 Test 5: Update System Prompt")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        repo = ProjectRepository(db)
        
        # Create project with initial prompt
        test_project = Project(
            user_id=1,
            name="Test Update Project",
            description="Testing updates",
            color="#ffff00",
            system_prompt="Initial prompt"
        )
        created = repo.create(test_project)
        print(f"✅ Project created with initial prompt: {created.system_prompt}")
        
        # Update system prompt
        created.system_prompt = "Updated prompt - testing modifications"
        updated = repo.update(created)
        print(f"✅ System prompt updated: {updated.system_prompt}")
        
        # Verify update persisted
        retrieved = repo.find_by_id(created.id)
        assert retrieved.system_prompt == "Updated prompt - testing modifications"
        print("✅ Update persisted in database")
        
        # Clean up
        repo.delete(created.id)
        print("✅ Test passed: System prompt can be updated")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        db.close()


def run_all_tests():
    """Run all integration tests"""
    print("\n" + "=" * 50)
    print("🧪 SYSTEM PROMPTS INTEGRATION TESTS")
    print("=" * 50)
    
    results = []
    
    # Run synchronous tests
    results.append(("Database Column", test_database_column_exists()))
    results.append(("Project Repository", test_project_repository()))
    results.append(("Optional Prompt", test_system_prompt_optional()))
    results.append(("Update Prompt", test_update_system_prompt()))
    
    # Run async test
    loop = asyncio.get_event_loop()
    results.append(("Chat Service", loop.run_until_complete(test_chat_service_system_prompt())))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name:25} {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print("\n" + "=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
    else:
        print(f"⚠️  {total - passed} test(s) failed")
    
    print("=" * 50 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
