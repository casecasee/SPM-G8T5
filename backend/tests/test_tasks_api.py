# """
# Test tasks API to verify it's working
# Run with: python backend/tests/test_tasks_api.py
# """

# import requests
# import json

# TASKS_SERVICE_URL = "http://localhost:5002"

# def test_tasks_api():
#     """Test the tasks API endpoints"""
#     print("🧪 Testing Tasks API")
#     print("=" * 30)
    
#     # Test 1: Get tasks
#     print("\n1️⃣ Testing GET /task...")
#     try:
#         response = requests.get(f"{TASKS_SERVICE_URL}/task", 
#                               params={"eid": 3, "role": "staff"},
#                               timeout=10)
        
#         print(f"   Status: {response.status_code}")
#         print(f"   Response: {response.text[:200]}...")
        
#         if response.status_code == 200:
#             data = response.json()
#             if 'tasks' in data:
#                 print(f"   ✅ Found 'tasks' property with {len(data['tasks'])} tasks")
#             else:
#                 print(f"   ❌ No 'tasks' property in response")
#                 print(f"   Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
#                 return False
#         else:
#             print(f"   ❌ API error: {response.text}")
#             return False
#     except Exception as e:
#         print(f"   ❌ Request error: {e}")
#         return False
    
#     # Test 2: Create a task
#     print("\n2️⃣ Testing POST /task...")
#     try:
#         task_data = {
#             "title": "Test Task",
#             "description": "Testing task creation",
#             "deadline": "2025-01-15T10:00:00Z",
#             "status": "ongoing",
#             "priority": 5,
#             "owner": 3,
#             "collaborators": [4, 5],
#             "employee_id": 3,
#             "role": "staff"
#         }
        
#         response = requests.post(f"{TASKS_SERVICE_URL}/task", 
#                                json=task_data,
#                                timeout=10)
        
#         print(f"   Status: {response.status_code}")
#         print(f"   Response: {response.text}")
        
#         if response.status_code in [200, 201]:
#             print("   ✅ Task created successfully")
#         else:
#             print(f"   ❌ Task creation failed: {response.text}")
#             return False
#     except Exception as e:
#         print(f"   ❌ Request error: {e}")
#         return False
    
#     # Test 3: Verify task appears in list
#     print("\n3️⃣ Testing task appears in list...")
#     try:
#         response = requests.get(f"{TASKS_SERVICE_URL}/task", 
#                               params={"eid": 3, "role": "staff"},
#                               timeout=10)
        
#         if response.status_code == 200:
#             data = response.json()
#             tasks = data.get('tasks', [])
#             test_tasks = [t for t in tasks if t.get('title') == 'Test Task']
            
#             if test_tasks:
#                 print(f"   ✅ Test task found in list: {test_tasks[0]['task_id']}")
#             else:
#                 print(f"   ❌ Test task not found in list")
#                 print(f"   Available tasks: {[t.get('title') for t in tasks]}")
#                 return False
#         else:
#             print(f"   ❌ Failed to get tasks: {response.text}")
#             return False
#     except Exception as e:
#         print(f"   ❌ Request error: {e}")
#         return False
    
#     print("\n" + "=" * 30)
#     print("🎉 ALL TESTS PASSED!")
#     print("✅ Tasks API is working correctly!")
#     return True

# if __name__ == "__main__":
#     test_tasks_api()
