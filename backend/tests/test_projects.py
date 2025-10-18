# backend/tests/test_projects.py
import unittest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Import the projects app and models
from projects.app import app, db
from models.project import Project
from models.staff import Staff


class TestProjectsAPI(unittest.TestCase):
    """Test the Projects API endpoints and functionality"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests"""
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        app.config["SQLALCHEMY_SESSION_OPTIONS"] = {"expire_on_commit": False}

        cls.app = app
        cls.client = app.test_client()
        
        with app.app_context():
            db.create_all()
            
            # Create test staff members
            staff1 = Staff(
                employee_name="John Doe", 
                email="john@example.com", 
                role="staff", 
                department="IT", 
                team="A", 
                password="Test123"
            )
            staff2 = Staff(
                employee_name="Jane Smith", 
                email="jane@example.com", 
                role="manager", 
                department="IT", 
                team="A", 
                password="Test123"
            )
            staff3 = Staff(
                employee_name="Bob Wilson", 
                email="bob@example.com", 
                role="staff", 
                department="Finance", 
                team="B", 
                password="Test123"
            )
            
            db.session.add_all([staff1, staff2, staff3])
            db.session.commit()
            
            # Store IDs for use in tests
            cls.staff1_id = staff1.employee_id
            cls.staff2_id = staff2.employee_id
            cls.staff3_id = staff3.employee_id

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        with cls.app.app_context():
            db.drop_all()

    def setUp(self):
        """Set up fresh state before each test"""
        with self.app.app_context():
            # Clean up any existing projects
            Project.query.delete()
            db.session.commit()

    def tearDown(self):
        """Clean up after each test"""
        with self.app.app_context():
            # Clean up projects created during test
            Project.query.delete()
            db.session.commit()

    # ----------------------------------------------------------------------
    # Test Project Creation
    # ----------------------------------------------------------------------

    def test_create_project_basic(self):
        """Test creating a project with minimal data"""
        payload = {
            "name": "Test Project",
            "owner": "John Doe",
            "ownerId": self.staff1_id,
            "status": "Active"
        }
        
        response = self.client.post("/projects", json=payload)
        
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        
        # Verify response structure
        self.assertIn("id", data)
        self.assertEqual(data["name"], "Test Project")
        self.assertEqual(data["owner"], "John Doe")
        self.assertEqual(data["ownerId"], self.staff1_id)
        self.assertEqual(data["status"], "Active")
        self.assertEqual(data["tasksDone"], 0)
        self.assertEqual(data["tasksTotal"], 0)
        self.assertIsNone(data["dueDate"])
        self.assertIn("updatedAt", data)
        self.assertEqual(data["memberIds"], [])
        self.assertEqual(data["memberNames"], [])

    def test_create_project_with_members(self):
        """Test creating a project with team members"""
        payload = {
            "name": "Team Project",
            "owner": "Jane Smith",
            "ownerId": self.staff2_id,
            "status": "Active",
            "members": [self.staff1_id, self.staff3_id]
        }
        
        response = self.client.post("/projects", json=payload)
        
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        
        # Verify members are included
        self.assertEqual(set(data["memberIds"]), {self.staff1_id, self.staff3_id})
        self.assertEqual(set(data["memberNames"]), {"John Doe", "Bob Wilson"})

    def test_create_project_with_due_date(self):
        """Test creating a project with a due date"""
        due_date = (datetime.utcnow() + timedelta(days=30)).isoformat() + "Z"
        
        payload = {
            "name": "Project with Deadline",
            "owner": "John Doe",
            "ownerId": self.staff1_id,
            "status": "Active",
            "dueDate": due_date
        }
        
        response = self.client.post("/projects", json=payload)
        
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        
        # Verify due date is set
        self.assertIsNotNone(data["dueDate"])
        self.assertIn("T", data["dueDate"])  # Should be ISO format

    def test_create_project_defaults(self):
        """Test creating a project with minimal data uses defaults"""
        payload = {}  # Empty payload
        
        response = self.client.post("/projects", json=payload)
        
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        
        # Verify defaults are applied
        self.assertEqual(data["name"], "Untitled Project")
        self.assertEqual(data["owner"], "Unassigned")
        self.assertIsNone(data["ownerId"])
        self.assertEqual(data["status"], "Active")
        self.assertEqual(data["tasksDone"], 0)
        self.assertEqual(data["tasksTotal"], 0)

    def test_create_project_invalid_due_date(self):
        """Test creating a project with invalid due date format"""
        payload = {
            "name": "Invalid Date Project",
            "owner": "John Doe",
            "ownerId": self.staff1_id,
            "dueDate": "invalid-date-format"
        }
        
        response = self.client.post("/projects", json=payload)
        
        # Should still succeed but with null due date
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertIsNone(data["dueDate"])

    # ----------------------------------------------------------------------
    # Test Project Listing
    # ----------------------------------------------------------------------

    def test_list_projects_empty(self):
        """Test listing projects when none exist"""
        response = self.client.get("/projects")
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data, [])

    def test_list_projects_with_data(self):
        """Test listing projects with existing data"""
        # Create test projects
        with self.app.app_context():
            project1 = Project(
                name="Project 1",
                owner="John Doe",
                owner_id=self.staff1_id,
                status="Active"
            )
            project2 = Project(
                name="Project 2",
                owner="Jane Smith",
                owner_id=self.staff2_id,
                status="On Hold"
            )
            
            db.session.add_all([project1, project2])
            db.session.commit()
            
            # Add members to project1
            staff1 = Staff.query.get(self.staff1_id)
            staff2 = Staff.query.get(self.staff2_id)
            project1.members.append(staff1)
            project1.members.append(staff2)
            db.session.commit()
        
        response = self.client.get("/projects")
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        # Should return 2 projects
        self.assertEqual(len(data), 2)
        
        # Should be ordered by updated_at desc (newest first)
        project_names = [p["name"] for p in data]
        self.assertIn("Project 1", project_names)
        self.assertIn("Project 2", project_names)
        
        # Verify project1 has members
        project1_data = next(p for p in data if p["name"] == "Project 1")
        self.assertEqual(len(project1_data["memberIds"]), 2)

    @patch('projects.app.Task')
    def test_list_projects_with_task_counts(self, mock_task_class):
        """Test that project listing includes task counts from tasks service"""
        # Create a test project
        with self.app.app_context():
            project = Project(
                name="Project with Tasks",
                owner="John Doe",
                owner_id=self.staff1_id,
                status="Active"
            )
            db.session.add(project)
            db.session.commit()
            project_id = project.id
        
        # Mock Task.query.all() to return tasks
        mock_task1 = MagicMock()
        mock_task1.project_id = project_id
        mock_task1.task_id = 1
        mock_task1.status = "done"
        
        mock_task2 = MagicMock()
        mock_task2.project_id = project_id
        mock_task2.task_id = 2
        mock_task2.status = "ongoing"
        
        mock_task3 = MagicMock()
        mock_task3.project_id = 999  # Different project
        mock_task3.task_id = 3
        mock_task3.status = "done"
        
        mock_task_class.query.all.return_value = [mock_task1, mock_task2, mock_task3]
        
        response = self.client.get("/projects")
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        # Find our project
        project_data = next(p for p in data if p["name"] == "Project with Tasks")
        
        # Should have correct task counts
        self.assertEqual(project_data["tasksTotal"], 2)  # 2 tasks for this project
        self.assertEqual(project_data["tasksDone"], 1)   # 1 done task

    @patch('projects.app.Task')
    def test_list_projects_task_query_error(self, mock_task_class):
        """Test that project listing handles task query errors gracefully"""
        # Create a test project
        with self.app.app_context():
            project = Project(
                name="Project with Error",
                owner="John Doe",
                owner_id=self.staff1_id,
                status="Active"
            )
            db.session.add(project)
            db.session.commit()
        
        # Mock Task.query.all() to raise an exception
        mock_task_class.query.all.side_effect = Exception("Database error")
        
        response = self.client.get("/projects")
        
        # Should still succeed but without task counts
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        project_data = next(p for p in data if p["name"] == "Project with Error")
        self.assertEqual(project_data["tasksTotal"], 0)  # Default values
        self.assertEqual(project_data["tasksDone"], 0)

    # ----------------------------------------------------------------------
    # Test Project Model
    # ----------------------------------------------------------------------

    def test_project_to_dict(self):
        """Test Project.to_dict() method"""
        with self.app.app_context():
            # Create project with members
            project = Project(
                name="Test Project",
                owner="John Doe",
                owner_id=self.staff1_id,
                status="Active",
                tasks_done=5,
                tasks_total=10
            )
            db.session.add(project)
            db.session.commit()
            
            # Add members
            staff1 = Staff.query.get(self.staff1_id)
            staff2 = Staff.query.get(self.staff2_id)
            project.members.append(staff1)
            project.members.append(staff2)
            db.session.commit()
            
            # Test to_dict()
            result = project.to_dict()
            
            # Verify all fields are present
            expected_keys = {
                "id", "name", "owner", "ownerId", "status", 
                "tasksDone", "tasksTotal", "dueDate", "updatedAt",
                "memberIds", "memberNames"
            }
            self.assertEqual(set(result.keys()), expected_keys)
            
            # Verify values
            self.assertEqual(result["name"], "Test Project")
            self.assertEqual(result["owner"], "John Doe")
            self.assertEqual(result["ownerId"], self.staff1_id)
            self.assertEqual(result["status"], "Active")
            self.assertEqual(result["tasksDone"], 5)
            self.assertEqual(result["tasksTotal"], 10)
            self.assertIsNone(result["dueDate"])
            self.assertIn("T", result["updatedAt"])  # ISO format
            self.assertEqual(set(result["memberIds"]), {self.staff1_id, self.staff2_id})
            self.assertEqual(set(result["memberNames"]), {"John Doe", "Jane Smith"})

    def test_project_with_due_date_to_dict(self):
        """Test Project.to_dict() with due date"""
        with self.app.app_context():
            due_date = datetime.utcnow() + timedelta(days=30)
            project = Project(
                name="Project with Due Date",
                owner="John Doe",
                owner_id=self.staff1_id,
                status="Active",
                due_date=due_date
            )
            db.session.add(project)
            db.session.commit()
            
            result = project.to_dict()
            
            # Verify due date format
            self.assertIsNotNone(result["dueDate"])
            self.assertIn("T", result["dueDate"])
            self.assertTrue(result["dueDate"].endswith("Z"))

    # ----------------------------------------------------------------------
    # Test Edge Cases
    # ----------------------------------------------------------------------

    def test_create_project_with_nonexistent_members(self):
        """Test creating project with non-existent member IDs"""
        payload = {
            "name": "Project with Bad Members",
            "owner": "John Doe",
            "ownerId": self.staff1_id,
            "members": [999, 998]  # Non-existent IDs
        }
        
        response = self.client.post("/projects", json=payload)
        
        # Should still succeed but with no members
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data["memberIds"], [])

    def test_create_project_malformed_json(self):
        """Test creating project with malformed JSON"""
        response = self.client.post(
            "/projects", 
            data="invalid json",
            content_type="application/json"
        )
        
        # Should handle gracefully
        self.assertIn(response.status_code, [400, 500])

    def test_list_projects_large_dataset(self):
        """Test listing projects with many projects"""
        with self.app.app_context():
            # Create many projects
            projects = []
            for i in range(50):
                project = Project(
                    name=f"Project {i}",
                    owner=f"Owner {i}",
                    owner_id=self.staff1_id,
                    status="Active"
                )
                projects.append(project)
            
            db.session.add_all(projects)
            db.session.commit()
        
        response = self.client.get("/projects")
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 50)
        
        # Should be ordered by updated_at desc
        for i in range(len(data) - 1):
            current_time = datetime.fromisoformat(data[i]["updatedAt"].replace("Z", "+00:00"))
            next_time = datetime.fromisoformat(data[i + 1]["updatedAt"].replace("Z", "+00:00"))
            self.assertGreaterEqual(current_time, next_time)


if __name__ == "__main__":
    unittest.main()
