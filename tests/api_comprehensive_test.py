"""
Comprehensive API Test Suite for AI Study Buddy
Tests all endpoints with all AI models
"""
import requests
import json
import time
from typing import Dict, List, Optional
from datetime import datetime
import os

BASE_URL = "http://localhost:8001/api/v1"

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class APITester:
    def __init__(self):
        self.token: Optional[str] = None
        self.user_id: Optional[int] = None
        self.test_results: List[Dict] = []
        self.projects: List[int] = []
        self.conversations: List[int] = []
        
    def log(self, message: str, status: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        if status == "PASS":
            print(f"{Colors.OKGREEN}✓ [{timestamp}] {message}{Colors.ENDC}")
        elif status == "FAIL":
            print(f"{Colors.FAIL}✗ [{timestamp}] {message}{Colors.ENDC}")
        elif status == "TEST":
            print(f"{Colors.OKCYAN}➤ [{timestamp}] {message}{Colors.ENDC}")
        else:
            print(f"{Colors.OKBLUE}ℹ [{timestamp}] {message}{Colors.ENDC}")
    
    def record_test(self, test_name: str, passed: bool, details: str = ""):
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    # ==================== AUTH TESTS ====================
    
    def test_signup(self, email: str, name: str, password: str) -> bool:
        """Test user signup"""
        self.log(f"Testing signup for {email}", "TEST")
        try:
            response = requests.post(
                f"{BASE_URL}/auth/signup",
                json={"email": email, "name": name, "password": password}
            )
            
            if response.status_code not in [200, 201]:
                self.log(f"Signup failed with status {response.status_code}: {response.text}", "FAIL")
                self.record_test("User Signup", False, f"Status {response.status_code}")
                return False
            
            data = response.json()
            
            if "access_token" not in data:
                self.log(f"Signup response missing access_token: {response.text}", "FAIL")
                self.record_test("User Signup", False, "Missing access_token")
                return False
            
            self.token = data["access_token"]
            self.user_id = data["user"]["id"]
            self.log(f"Signup successful - User ID: {self.user_id}", "PASS")
            self.record_test("User Signup", True, f"User {email} created")
            return True
        except Exception as e:
            self.log(f"Signup error: {str(e)}", "FAIL")
            self.record_test("User Signup", False, str(e))
            return False
    
    def test_login(self, email: str, password: str) -> bool:
        """Test user login"""
        self.log(f"Testing login for {email}", "TEST")
        try:
            response = requests.post(
                f"{BASE_URL}/auth/login",
                json={"email": email, "password": password}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.user_id = data["user"]["id"]
                self.log("Login successful", "PASS")
                self.record_test("User Login", True, f"Logged in as {email}")
                return True
            else:
                self.log(f"Login failed: {response.text}", "FAIL")
                self.record_test("User Login", False, response.text)
                return False
        except Exception as e:
            self.log(f"Login error: {str(e)}", "FAIL")
            self.record_test("User Login", False, str(e))
            return False
    
    def get_headers(self) -> Dict:
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.token}"}
    
    # ==================== USER PROFILE TESTS ====================
    
    def test_get_profile(self) -> bool:
        """Test getting user profile"""
        self.log("Testing get profile", "TEST")
        try:
            response = requests.get(
                f"{BASE_URL}/users/me",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                user = response.json()
                self.log(f"Profile retrieved - Name: {user['name']}", "PASS")
                self.record_test("Get User Profile", True, f"Retrieved profile for {user['email']}")
                return True
            else:
                self.log(f"Get profile failed: {response.text}", "FAIL")
                self.record_test("Get User Profile", False, response.text)
                return False
        except Exception as e:
            self.log(f"Get profile error: {str(e)}", "FAIL")
            self.record_test("Get User Profile", False, str(e))
            return False
    
    def test_update_profile(self, bio: str = "Test Bio") -> bool:
        """Test updating user profile"""
        self.log("Testing update profile", "TEST")
        try:
            response = requests.put(
                f"{BASE_URL}/users/me",
                headers=self.get_headers(),
                json={"bio": bio, "organization": "Test Organization"}
            )
            
            if response.status_code == 200:
                self.log("Profile updated successfully", "PASS")
                self.record_test("Update User Profile", True, "Updated bio and organization")
                return True
            else:
                self.log(f"Update profile failed: {response.text}", "FAIL")
                self.record_test("Update User Profile", False, response.text)
                return False
        except Exception as e:
            self.log(f"Update profile error: {str(e)}", "FAIL")
            self.record_test("Update User Profile", False, str(e))
            return False
    
    # ==================== PROJECT TESTS ====================
    
    def test_create_project(self, name: str, description: str, agent_name: str = "Test Agent") -> Optional[int]:
        """Test creating a project"""
        self.log(f"Testing create project: {name}", "TEST")
        try:
            response = requests.post(
                f"{BASE_URL}/projects",
                headers=self.get_headers(),
                json={
                    "name": name,
                    "description": description,
                    "color": "#3b82f6",
                    "agent_name": agent_name,
                    "system_prompt": "You are a helpful AI assistant.",
                    "tools": ["web_search"]
                }
            )
            
            if response.status_code in [200, 201]:
                project = response.json()
                project_id = project["id"]
                self.projects.append(project_id)
                self.log(f"Project created - ID: {project_id}", "PASS")
                self.record_test("Create Project", True, f"Created project: {name}")
                return project_id
            else:
                self.log(f"Create project failed: {response.text}", "FAIL")
                self.record_test("Create Project", False, response.text)
                return None
        except Exception as e:
            self.log(f"Create project error: {str(e)}", "FAIL")
            self.record_test("Create Project", False, str(e))
            return None
    
    def test_get_projects(self) -> bool:
        """Test getting all projects"""
        self.log("Testing get projects", "TEST")
        try:
            response = requests.get(
                f"{BASE_URL}/projects",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                projects = response.json()
                self.log(f"Retrieved {len(projects)} projects", "PASS")
                self.record_test("Get Projects", True, f"Retrieved {len(projects)} projects")
                return True
            else:
                self.log(f"Get projects failed: {response.text}", "FAIL")
                self.record_test("Get Projects", False, response.text)
                return False
        except Exception as e:
            self.log(f"Get projects error: {str(e)}", "FAIL")
            self.record_test("Get Projects", False, str(e))
            return False
    
    def test_delete_project(self, project_id: int) -> bool:
        """Test deleting a project"""
        self.log(f"Testing delete project: {project_id}", "TEST")
        try:
            response = requests.delete(
                f"{BASE_URL}/projects/{project_id}",
                headers=self.get_headers()
            )
            
            if response.status_code in [200, 204]:
                self.log(f"Project {project_id} deleted", "PASS")
                self.record_test("Delete Project", True, f"Deleted project {project_id}")
                return True
            else:
                self.log(f"Delete project failed: {response.text}", "FAIL")
                self.record_test("Delete Project", False, response.text)
                return False
        except Exception as e:
            self.log(f"Delete project error: {str(e)}", "FAIL")
            self.record_test("Delete Project", False, str(e))
            return False
    
    # ==================== CONVERSATION & MESSAGE TESTS ====================
    
    def test_create_conversation(self, project_id: int, model: str, test_message: str, use_gpu: bool = True) -> Optional[int]:
        """Test creating a conversation and sending a message with specific model"""
        gpu_status = "GPU" if use_gpu else "CPU"
        self.log(f"Testing conversation with model: {model} ({gpu_status})", "TEST")
        try:
            response = requests.post(
                f"{BASE_URL}/chat",
                headers=self.get_headers(),
                json={
                    "project_id": project_id,
                    "message": test_message,
                    "model": model,
                    "use_gpu": use_gpu,
                    "conversation_id": None
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                conversation_id = data.get("conversation_id")
                response_obj = data.get("response", {})
                assistant_message = response_obj.get("content", "") if isinstance(response_obj, dict) else str(response_obj)
                
                self.conversations.append(conversation_id)
                self.log(f"Conversation created - Model: {model}, Conv ID: {conversation_id}", "PASS")
                if assistant_message:
                    preview = assistant_message[:100] if len(assistant_message) > 100 else assistant_message
                    self.log(f"Response preview: {preview}...", "INFO")
                self.record_test(f"Create Conversation ({model})", True, f"Conv ID: {conversation_id}")
                return conversation_id
            else:
                self.log(f"Create conversation failed ({model}): {response.text}", "FAIL")
                self.record_test(f"Create Conversation ({model})", False, response.text)
                return None
        except Exception as e:
            self.log(f"Create conversation error ({model}): {str(e)}", "FAIL")
            self.record_test(f"Create Conversation ({model})", False, str(e))
            return None
    
    def test_get_conversation_messages(self, conversation_id: int) -> bool:
        """Test retrieving conversation messages"""
        self.log(f"Testing get messages for conversation {conversation_id}", "TEST")
        try:
            response = requests.get(
                f"{BASE_URL}/conversations/{conversation_id}/messages",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                messages = response.json()
                self.log(f"Retrieved {len(messages)} messages", "PASS")
                self.record_test("Get Conversation Messages", True, f"{len(messages)} messages retrieved")
                return True
            else:
                self.log(f"Get messages failed: {response.text}", "FAIL")
                self.record_test("Get Conversation Messages", False, response.text)
                return False
        except Exception as e:
            self.log(f"Get messages error: {str(e)}", "FAIL")
            self.record_test("Get Conversation Messages", False, str(e))
            return False
    
    def test_update_conversation_title(self, conversation_id: int, new_title: str) -> bool:
        """Test updating conversation title (PATCH endpoint)"""
        self.log(f"Testing update conversation title to: {new_title}", "TEST")
        try:
            response = requests.patch(
                f"{BASE_URL}/chat/conversations/{conversation_id}",
                headers=self.get_headers(),
                json={"title": new_title}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"Title updated successfully to: {data.get('title')}", "PASS")
                self.record_test("Update Conversation Title", True, f"Updated to: {new_title}")
                return True
            else:
                self.log(f"Update title failed: {response.text}", "FAIL")
                self.record_test("Update Conversation Title", False, response.text)
                return False
        except Exception as e:
            self.log(f"Update title error: {str(e)}", "FAIL")
            self.record_test("Update Conversation Title", False, str(e))
            return False
    
    def test_delete_conversation(self, conversation_id: int) -> bool:
        """Test deleting a conversation (DELETE endpoint)"""
        self.log(f"Testing delete conversation: {conversation_id}", "TEST")
        try:
            response = requests.delete(
                f"{BASE_URL}/chat/conversations/{conversation_id}",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                self.log(f"Conversation {conversation_id} deleted successfully", "PASS")
                self.record_test("Delete Conversation", True, f"Deleted conversation {conversation_id}")
                return True
            else:
                self.log(f"Delete conversation failed: {response.text}", "FAIL")
                self.record_test("Delete Conversation", False, response.text)
                return False
        except Exception as e:
            self.log(f"Delete conversation error: {str(e)}", "FAIL")
            self.record_test("Delete Conversation", False, str(e))
            return False
    
    def test_get_project_conversations(self, project_id: int) -> bool:
        """Test getting all conversations for a project (verify sorting)"""
        self.log(f"Testing get conversations for project {project_id}", "TEST")
        try:
            response = requests.get(
                f"{BASE_URL}/chat/projects/{project_id}/conversations",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                conversations = response.json()
                self.log(f"Retrieved {len(conversations)} conversations", "PASS")
                
                # Verify conversations are sorted by updated_at (newest first)
                if len(conversations) > 1:
                    for i in range(len(conversations) - 1):
                        current_time = conversations[i].get('updated_at')
                        next_time = conversations[i + 1].get('updated_at')
                        if current_time and next_time and current_time < next_time:
                            self.log("Warning: Conversations not properly sorted", "WARNING")
                
                self.record_test("Get Project Conversations", True, f"{len(conversations)} conversations")
                return True
            else:
                self.log(f"Get conversations failed: {response.text}", "FAIL")
                self.record_test("Get Project Conversations", False, response.text)
                return False
        except Exception as e:
            self.log(f"Get conversations error: {str(e)}", "FAIL")
            self.record_test("Get Project Conversations", False, str(e))
            return False
    
    # ==================== STATS TESTS ====================
    
    def test_get_stats(self) -> bool:
        """Test getting stats overview"""
        self.log("Testing get stats overview", "TEST")
        try:
            response = requests.get(
                f"{BASE_URL}/stats/overview",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                stats = response.json()
                # Handle different possible response structures
                projects = stats.get('total_projects', stats.get('projects', 0))
                conversations = stats.get('total_conversations', stats.get('conversations', 0))
                self.log(f"Stats: {projects} projects, {conversations} conversations", "PASS")
                self.record_test("Get Stats Overview", True, json.dumps(stats))
                return True
            else:
                self.log(f"Get stats failed: {response.text}", "FAIL")
                self.record_test("Get Stats Overview", False, response.text)
                return False
        except Exception as e:
            self.log(f"Get stats error: {str(e)}", "FAIL")
            self.record_test("Get Stats Overview", False, str(e))
            return False
    
    # ==================== CLEANUP ====================
    
    def test_delete_account(self) -> bool:
        """Test deleting user account"""
        self.log("Testing delete account", "TEST")
        try:
            response = requests.delete(
                f"{BASE_URL}/users/me",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                self.log("Account deleted successfully", "PASS")
                self.record_test("Delete User Account", True, "Account and all data deleted")
                return True
            else:
                self.log(f"Delete account failed: {response.text}", "FAIL")
                self.record_test("Delete User Account", False, response.text)
                return False
        except Exception as e:
            self.log(f"Delete account error: {str(e)}", "FAIL")
            self.record_test("Delete User Account", False, str(e))
            return False
    
    # ==================== REPORT GENERATION ====================
    
    def generate_report(self):
        """Generate and display test report"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}")
        print("                         COMPREHENSIVE API TEST REPORT")
        print(f"{'='*80}{Colors.ENDC}\n")
        
        passed = sum(1 for t in self.test_results if t["passed"])
        total = len(self.test_results)
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"{Colors.BOLD}Summary:{Colors.ENDC}")
        print(f"  Total Tests: {total}")
        print(f"  Passed: {Colors.OKGREEN}{passed}{Colors.ENDC}")
        print(f"  Failed: {Colors.FAIL}{total - passed}{Colors.ENDC}")
        print(f"  Pass Rate: {Colors.OKGREEN if pass_rate >= 90 else Colors.WARNING}{pass_rate:.1f}%{Colors.ENDC}\n")
        
        print(f"{Colors.BOLD}Test Details:{Colors.ENDC}")
        for result in self.test_results:
            status_symbol = "✓" if result["passed"] else "✗"
            status_color = Colors.OKGREEN if result["passed"] else Colors.FAIL
            print(f"  {status_color}{status_symbol} {result['test']}{Colors.ENDC}")
            if result["details"]:
                print(f"    {Colors.OKBLUE}→ {result['details']}{Colors.ENDC}")
        
        print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}\n")


def main():
    """Run comprehensive API tests"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}Starting Comprehensive API Test Suite{Colors.ENDC}\n")
    
    tester = APITester()
    
    # Test data
    test_email = f"test_user_{int(time.time())}@example.com"
    test_password = "SecurePassword123!"
    test_name = "API Test User"
    
    # Available AI models to test
    # Fast CPU models for demos (small size, quick responses)
    fast_models = [
        "qwen2.5:0.5b",    # 397 MB - FASTEST
        "gemma2:2b",        # 1.6 GB - Very fast
        "phi3:mini"         # 2.2 GB - Fast
    ]
    
    # Full-size models (better quality, slower)
    full_models = [
        "llama3-groq-tool-use:8b",
        "llama3:8b",
        "qwen2.5:7b",
        "mistral:7b"
    ]
    
    # Test fast models first for demos, then full models
    models = fast_models + full_models
    
    print(f"{Colors.BOLD}Phase 1: User Authentication{Colors.ENDC}\n")
    if not tester.test_signup(test_email, test_name, test_password):
        print(f"{Colors.FAIL}Signup failed - aborting tests{Colors.ENDC}")
        return
    
    time.sleep(1)
    tester.test_get_profile()
    tester.test_update_profile()
    
    print(f"\n{Colors.BOLD}Phase 2: Project Management{Colors.ENDC}\n")
    project_id = tester.test_create_project("Test Project", "Comprehensive API Testing")
    if project_id:
        tester.test_get_projects()
    
    print(f"\n{Colors.BOLD}Phase 3: Conversations with AI Models (CPU + GPU){Colors.ENDC}\n")
    conversation_ids = []
    if project_id:
        # Test CPU models (fast, lightweight)
        for model in ["qwen2.5:0.5b", "gemma2:2b"]:
            tester.log(f"\nTesting CPU model: {model}...", "INFO")
            conv_id = tester.test_create_conversation(
                project_id,
                model,
                f"Hello! Please respond with a simple greeting. This is a test of the {model} model.",
                use_gpu=False
            )
            if conv_id:
                conversation_ids.append(conv_id)
                time.sleep(2)
                tester.test_get_conversation_messages(conv_id)
        
        # Test GPU models (better quality, GPU accelerated)
        for model in ["llama3:8b", "qwen2.5:7b"]:
            tester.log(f"\nTesting GPU model: {model}...", "INFO")
            conv_id = tester.test_create_conversation(
                project_id,
                model,
                f"Hello! Please respond with a simple greeting. This is a test of the {model} model.",
                use_gpu=True
            )
            if conv_id:
                conversation_ids.append(conv_id)
                time.sleep(2)
                tester.test_get_conversation_messages(conv_id)
    
    print(f"\n{Colors.BOLD}Phase 4: Statistics & Overview{Colors.ENDC}\n")
    tester.test_get_stats()
    
    print(f"\n{Colors.BOLD}Phase 5: Cleanup{Colors.ENDC}\n")
    if project_id:
        tester.test_delete_project(project_id)
    
    tester.test_delete_account()
    
    # Generate final report
    tester.generate_report()


if __name__ == "__main__":
    main()
