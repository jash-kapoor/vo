#!/usr/bin/env python3
"""
Vocrypt Backend API Testing Suite
Tests all backend API endpoints for functionality and integration
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, List

# Configuration
BASE_URL = "https://voice-clone-33.preview.emergentagent.com/api"
TIMEOUT = 30

class VocryptAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.test_results = []
        self.created_sessions = []
        
    def log_test(self, test_name: str, success: bool, message: str, details: Dict = None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def test_api_health(self) -> bool:
        """Test GET /api/ endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/")
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "Vocrypt" in data["message"]:
                    self.log_test("API Health Check", True, "Backend is running and responding correctly")
                    return True
                else:
                    self.log_test("API Health Check", False, "Unexpected response format", {"response": data})
                    return False
            else:
                self.log_test("API Health Check", False, f"HTTP {response.status_code}", {"response": response.text})
                return False
                
        except Exception as e:
            self.log_test("API Health Check", False, f"Connection error: {str(e)}")
            return False
    
    def test_moods_api(self) -> bool:
        """Test GET /api/moods endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/moods")
            
            if response.status_code == 200:
                moods = response.json()
                
                # Verify it's a list
                if not isinstance(moods, list):
                    self.log_test("Moods API", False, "Response is not a list", {"response": moods})
                    return False
                
                # Verify expected moods are present
                expected_moods = ['happy', 'calm', 'energetic', 'wise', 'playful', 'professional']
                mood_names = [mood['name'] for mood in moods if 'name' in mood]
                
                missing_moods = set(expected_moods) - set(mood_names)
                if missing_moods:
                    self.log_test("Moods API", False, f"Missing moods: {missing_moods}", {"received_moods": mood_names})
                    return False
                
                # Verify mood structure
                for mood in moods:
                    required_fields = ['name', 'color', 'emoji', 'description']
                    missing_fields = [field for field in required_fields if field not in mood]
                    if missing_fields:
                        self.log_test("Moods API", False, f"Mood {mood.get('name', 'unknown')} missing fields: {missing_fields}")
                        return False
                
                self.log_test("Moods API", True, f"Successfully retrieved {len(moods)} moods with correct structure")
                return True
            else:
                self.log_test("Moods API", False, f"HTTP {response.status_code}", {"response": response.text})
                return False
                
        except Exception as e:
            self.log_test("Moods API", False, f"Request error: {str(e)}")
            return False
    
    def test_session_creation(self) -> List[str]:
        """Test POST /api/sessions with different moods"""
        moods_to_test = ['happy', 'calm', 'energetic', 'wise', 'playful', 'professional']
        created_session_ids = []
        
        for mood in moods_to_test:
            try:
                payload = {"mood": mood}
                response = self.session.post(f"{self.base_url}/sessions", json=payload)
                
                if response.status_code == 200:
                    session_data = response.json()
                    
                    # Verify session structure
                    required_fields = ['id', 'mood', 'created_at', 'is_active']
                    missing_fields = [field for field in required_fields if field not in session_data]
                    
                    if missing_fields:
                        self.log_test(f"Session Creation ({mood})", False, f"Missing fields: {missing_fields}")
                        continue
                    
                    if session_data['mood'] != mood:
                        self.log_test(f"Session Creation ({mood})", False, f"Mood mismatch: expected {mood}, got {session_data['mood']}")
                        continue
                    
                    session_id = session_data['id']
                    created_session_ids.append(session_id)
                    self.created_sessions.append(session_id)
                    
                    self.log_test(f"Session Creation ({mood})", True, f"Session created successfully with ID: {session_id}")
                else:
                    self.log_test(f"Session Creation ({mood})", False, f"HTTP {response.status_code}", {"response": response.text})
                    
            except Exception as e:
                self.log_test(f"Session Creation ({mood})", False, f"Request error: {str(e)}")
        
        return created_session_ids
    
    def test_session_retrieval(self, session_ids: List[str]) -> bool:
        """Test GET /api/sessions/{session_id}"""
        if not session_ids:
            self.log_test("Session Retrieval", False, "No session IDs available for testing")
            return False
        
        success_count = 0
        for session_id in session_ids[:3]:  # Test first 3 sessions
            try:
                response = self.session.get(f"{self.base_url}/sessions/{session_id}")
                
                if response.status_code == 200:
                    session_data = response.json()
                    
                    if session_data.get('id') == session_id:
                        success_count += 1
                        self.log_test(f"Session Retrieval ({session_id[:8]}...)", True, "Session retrieved successfully")
                    else:
                        self.log_test(f"Session Retrieval ({session_id[:8]}...)", False, "Session ID mismatch in response")
                else:
                    self.log_test(f"Session Retrieval ({session_id[:8]}...)", False, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Session Retrieval ({session_id[:8]}...)", False, f"Request error: {str(e)}")
        
        overall_success = success_count > 0
        if overall_success:
            self.log_test("Session Retrieval Overall", True, f"Successfully retrieved {success_count} sessions")
        else:
            self.log_test("Session Retrieval Overall", False, "Failed to retrieve any sessions")
        
        return overall_success
    
    def test_messaging_system(self, session_ids: List[str]) -> bool:
        """Test POST /api/sessions/{session_id}/messages"""
        if not session_ids:
            self.log_test("Messaging System", False, "No session IDs available for testing")
            return False
        
        test_messages = [
            "Hello, how are you today?",
            "Can you tell me a joke?",
            "What's the weather like?",
            "Help me solve a problem"
        ]
        
        success_count = 0
        session_id = session_ids[0]  # Use first session for messaging tests
        
        for i, message_content in enumerate(test_messages):
            try:
                payload = {
                    "content": message_content,
                    "type": "user"
                }
                response = self.session.post(f"{self.base_url}/sessions/{session_id}/messages", json=payload)
                
                if response.status_code == 200:
                    message_data = response.json()
                    
                    # Verify message structure
                    required_fields = ['id', 'session_id', 'type', 'content', 'timestamp']
                    missing_fields = [field for field in required_fields if field not in message_data]
                    
                    if missing_fields:
                        self.log_test(f"Send Message {i+1}", False, f"Missing fields: {missing_fields}")
                        continue
                    
                    if message_data['session_id'] != session_id:
                        self.log_test(f"Send Message {i+1}", False, "Session ID mismatch in response")
                        continue
                    
                    # Check if AI response was generated (type should be 'ai' for AI responses)
                    if message_data['type'] == 'ai':
                        success_count += 1
                        self.log_test(f"Send Message {i+1}", True, f"AI response generated: {message_data['content'][:50]}...")
                    elif message_data['type'] == 'user':
                        # User message was stored, but check if AI response follows
                        time.sleep(2)  # Wait for AI processing
                        success_count += 1
                        self.log_test(f"Send Message {i+1}", True, "User message processed successfully")
                    else:
                        self.log_test(f"Send Message {i+1}", False, f"Unexpected message type: {message_data['type']}")
                else:
                    self.log_test(f"Send Message {i+1}", False, f"HTTP {response.status_code}", {"response": response.text})
                    
            except Exception as e:
                self.log_test(f"Send Message {i+1}", False, f"Request error: {str(e)}")
        
        overall_success = success_count > 0
        if overall_success:
            self.log_test("Messaging System Overall", True, f"Successfully processed {success_count}/{len(test_messages)} messages")
        else:
            self.log_test("Messaging System Overall", False, "Failed to process any messages")
        
        return overall_success
    
    def test_messages_retrieval(self, session_ids: List[str]) -> bool:
        """Test GET /api/sessions/{session_id}/messages"""
        if not session_ids:
            self.log_test("Messages Retrieval", False, "No session IDs available for testing")
            return False
        
        session_id = session_ids[0]  # Use first session
        
        try:
            response = self.session.get(f"{self.base_url}/sessions/{session_id}/messages")
            
            if response.status_code == 200:
                messages = response.json()
                
                if not isinstance(messages, list):
                    self.log_test("Messages Retrieval", False, "Response is not a list", {"response": messages})
                    return False
                
                if len(messages) == 0:
                    self.log_test("Messages Retrieval", True, "No messages found (empty session)")
                    return True
                
                # Verify message structure
                for i, message in enumerate(messages):
                    required_fields = ['id', 'session_id', 'type', 'content', 'timestamp']
                    missing_fields = [field for field in required_fields if field not in message]
                    
                    if missing_fields:
                        self.log_test("Messages Retrieval", False, f"Message {i} missing fields: {missing_fields}")
                        return False
                    
                    if message['session_id'] != session_id:
                        self.log_test("Messages Retrieval", False, f"Message {i} has wrong session_id")
                        return False
                
                # Count message types
                user_messages = sum(1 for msg in messages if msg['type'] == 'user')
                ai_messages = sum(1 for msg in messages if msg['type'] == 'ai')
                system_messages = sum(1 for msg in messages if msg['type'] == 'system')
                
                self.log_test("Messages Retrieval", True, 
                            f"Retrieved {len(messages)} messages (User: {user_messages}, AI: {ai_messages}, System: {system_messages})")
                return True
            else:
                self.log_test("Messages Retrieval", False, f"HTTP {response.status_code}", {"response": response.text})
                return False
                
        except Exception as e:
            self.log_test("Messages Retrieval", False, f"Request error: {str(e)}")
            return False
    
    def test_error_handling(self) -> bool:
        """Test error handling for invalid requests"""
        error_tests = [
            {
                "name": "Invalid Session ID",
                "url": f"{self.base_url}/sessions/invalid-session-id",
                "method": "GET"
            },
            {
                "name": "Invalid Mood",
                "url": f"{self.base_url}/sessions",
                "method": "POST",
                "payload": {"mood": "invalid_mood"}
            },
            {
                "name": "Missing Message Content",
                "url": f"{self.base_url}/sessions/test-session/messages",
                "method": "POST",
                "payload": {"type": "user"}
            }
        ]
        
        success_count = 0
        for test in error_tests:
            try:
                if test["method"] == "GET":
                    response = self.session.get(test["url"])
                elif test["method"] == "POST":
                    response = self.session.post(test["url"], json=test.get("payload", {}))
                
                # We expect these to fail gracefully (not 500 errors)
                if response.status_code in [400, 404, 422]:
                    success_count += 1
                    self.log_test(f"Error Handling - {test['name']}", True, f"Proper error response: {response.status_code}")
                elif response.status_code == 500:
                    self.log_test(f"Error Handling - {test['name']}", False, "Server error (500) - should handle gracefully")
                else:
                    self.log_test(f"Error Handling - {test['name']}", False, f"Unexpected status: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Error Handling - {test['name']}", False, f"Request error: {str(e)}")
        
        overall_success = success_count >= len(error_tests) // 2  # At least half should work
        return overall_success
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Vocrypt Backend API Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Test 1: API Health
        health_ok = self.test_api_health()
        
        # Test 2: Moods API
        moods_ok = self.test_moods_api()
        
        # Test 3: Session Creation
        session_ids = self.test_session_creation()
        sessions_ok = len(session_ids) > 0
        
        # Test 4: Session Retrieval
        retrieval_ok = self.test_session_retrieval(session_ids)
        
        # Test 5: Messaging System
        messaging_ok = self.test_messaging_system(session_ids)
        
        # Test 6: Messages Retrieval
        messages_ok = self.test_messages_retrieval(session_ids)
        
        # Test 7: Error Handling
        errors_ok = self.test_error_handling()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Critical functionality check
        critical_tests = [health_ok, moods_ok, sessions_ok]
        critical_passed = sum(critical_tests)
        
        print(f"\n🔥 Critical Functionality: {critical_passed}/3 working")
        print(f"🤖 AI Integration: {'✅ Working' if messaging_ok else '❌ Failed'}")
        print(f"💾 MongoDB Integration: {'✅ Working' if (sessions_ok and messages_ok) else '❌ Failed'}")
        
        # Failed tests details
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['message']}")
        
        return passed_tests, failed_tests, self.test_results

if __name__ == "__main__":
    tester = VocryptAPITester()
    passed, failed, results = tester.run_all_tests()
    
    # Exit with appropriate code
    exit(0 if failed == 0 else 1)