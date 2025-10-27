# backend/tests/test_projects.py
import unittest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Import the projects app and models
from projects.app import app, db
from models.project import Project
from models.task import Task
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
            # Clean up any existing projects and their members
            Project.query.delete()
            # Explicitly clean up the association table
            db.session.execute(db.text("DELETE FROM project_members"))
            # Also clear tasks and their collaborators to avoid stale counts/id reuse
            db.session.execute(db.text("DELETE FROM task_collaborators"))
            Task.query.delete()
            db.session.commit()

    def tearDown(self):
        """Clean up after each test"""
        with self.app.app_context():
            # Clean up projects and their members created during test
            Project.query.delete()
            # Explicitly clean up the association table
            db.session.execute(db.text("DELETE FROM project_members"))
            # Clear tasks and collaborators as well
            db.session.execute(db.text("DELETE FROM task_collaborators"))
            Task.query.delete()
            db.session.commit()

    # ----------------------------------------------------------------------
    # Test Project Creation
    # ----------------------------------------------------------------------

    def test_create_project_basic(self):
        """Test creating a project with minimal data"""
        payload = {
            "name": "Test Project",
            "owner": "John Doe",
            "ownerId": self.staff1_id
        }
        
        response = self.client.post("/projects", json=payload)
        
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        
        # Verify response structure
        self.assertIn("id", data)
        self.assertEqual(data["name"], "Test Project")
        self.assertEqual(data["owner"], "John Doe")
        self.assertEqual(data["ownerId"], self.staff1_id)
        # status removed from API
        self.assertEqual(data["tasksDone"], 0)
        self.assertEqual(data["tasksTotal"], 0)
        self.assertIsNone(data["dueDate"])
        self.assertIn("updatedAt", data)
        # owner is auto-added as sole member
        self.assertEqual(data["memberIds"], [self.staff1_id])
        self.assertEqual(data["memberNames"], ["John Doe"])

    def test_create_project_with_members(self):
        """Test creating a project with team members"""
        payload = {
            "name": "Team Project",
            "owner": "Jane Smith",
            "ownerId": self.staff2_id,
            "members": [self.staff1_id, self.staff3_id]
        }
        
        response = self.client.post("/projects", json=payload)
        
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        
        # Verify members include provided AND owner (auto-added)
        self.assertEqual(set(data["memberIds"]), {self.staff2_id, self.staff1_id, self.staff3_id})
        self.assertEqual(set(data["memberNames"]), {"Jane Smith", "John Doe", "Bob Wilson"})

    def test_create_project_with_due_date(self):
        """Test creating a project with a due date"""
        due_date = (datetime.utcnow() + timedelta(days=30)).isoformat() + "Z"
        
        payload = {
            "name": "Project with Deadline",
            "owner": "John Doe",
            "ownerId": self.staff1_id,
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
        payload = {"ownerId": self.staff1_id}  # ownerId is required now
        
        response = self.client.post("/projects", json=payload)
        
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        
        # Verify defaults are applied
        self.assertEqual(data["name"], "Untitled Project")
        self.assertEqual(data["owner"], "Unassigned")
        self.assertEqual(data["ownerId"], self.staff1_id)
        # status removed from API
        self.assertEqual(data["tasksDone"], 0)
        self.assertEqual(data["tasksTotal"], 0)
        # owner auto-added as member
        self.assertEqual(data["memberIds"], [self.staff1_id])
        self.assertEqual(data["memberNames"], ["John Doe"])

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
                owner_id=self.staff1_id
            )
            project2 = Project(
                name="Project 2",
                owner="Jane Smith",
                owner_id=self.staff2_id
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

    def test_list_projects_staff_member_scope(self):
        """
        Staff should only see projects they are a member of.
        """
        # Create two projects: one with staff1 as member, one without
        with self.app.app_context():
            project_with_me = Project(name="Mine", owner="O", owner_id=self.staff2_id)
            project_without_me = Project(name="NotMine", owner="O", owner_id=self.staff2_id)
            db.session.add_all([project_with_me, project_without_me]); db.session.commit()

            me = Staff.query.get(self.staff1_id)  # staff1 is IT staff
            project_with_me.members.append(me)
            db.session.commit()

        # Run list in production mode (role filtering), with a staff session
        original_testing = self.app.config.get("TESTING", False)
        try:
            self.app.config["TESTING"] = False
            with self.client.session_transaction() as sess:
                sess["employee_id"] = self.staff1_id
                sess["role"] = "staff"
                sess["department"] = "IT"

            res = self.client.get("/projects")
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            names = {p["name"] for p in data}
            self.assertIn("Mine", names)
            self.assertNotIn("NotMine", names)
        finally:
            self.app.config["TESTING"] = original_testing

    def test_list_projects_manager_department_scope(self):
        """
        Manager should see projects in their department (even if not a member).
        """
        with self.app.app_context():
            # Project with IT member
            proj_it = Project(name="IT Project", owner="O", owner_id=self.staff2_id)
            # Project with Finance member
            proj_fin = Project(name="FIN Project", owner="O", owner_id=self.staff2_id)
            db.session.add_all([proj_it, proj_fin]); db.session.commit()

            it_member = Staff.query.get(self.staff1_id)     # department IT
            fin_member = Staff.query.get(self.staff3_id)    # department Finance
            proj_it.members.append(it_member)
            proj_fin.members.append(fin_member)
            db.session.commit()

        original_testing = self.app.config.get("TESTING", False)
        try:
            self.app.config["TESTING"] = False
            with self.client.session_transaction() as sess:
                sess["employee_id"] = self.staff2_id  # Jane Smith (manager, IT)
                sess["role"] = "manager"
                sess["department"] = "IT"

            res = self.client.get("/projects")
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            names = {p["name"] for p in data}
            self.assertIn("IT Project", names)
            self.assertNotIn("FIN Project", names)
        finally:
            self.app.config["TESTING"] = original_testing

    def test_list_projects_senior_manager_sees_all(self):
        """
        Senior manager (or HR/Director) should see all projects.
        """
        with self.app.app_context():
            p1 = Project(name="P1", owner="O", owner_id=self.staff1_id)
            p2 = Project(name="P2", owner="O", owner_id=self.staff2_id)
            db.session.add_all([p1, p2]); db.session.commit()

        original_testing = self.app.config.get("TESTING", False)
        try:
            self.app.config["TESTING"] = False
            with self.client.session_transaction() as sess:
                sess["employee_id"] = self.staff2_id
                sess["role"] = "senior manager"
                sess["department"] = "IT"

            res = self.client.get("/projects")
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            names = {p["name"] for p in data}
            self.assertIn("P1", names)
            self.assertIn("P2", names)
        finally:
            self.app.config["TESTING"] = original_testing

    # ----------------------------------------------------------------------
    # Task counts persisted
    # ----------------------------------------------------------------------

    def test_task_counts_persisted_to_db(self):
        """
        GET /projects should compute tasksTotal/tasksDone and persist them to the DB.
        """
        from models.task import Task

        with self.app.app_context():
            # Create two projects
            p1 = Project(name="Counts P1", owner="O", owner_id=self.staff1_id)
            p2 = Project(name="Counts P2", owner="O", owner_id=self.staff1_id)
            db.session.add_all([p1, p2]); db.session.commit()
            pid1, pid2 = p1.id, p2.id

            # Create tasks for p1: 3 total, 2 done; p2: 1 done
            t1 = Task(title="T1", description="D1",
                      deadline=datetime.utcnow() + timedelta(days=7),
                      status="done", owner=self.staff1_id,
                      project_id=pid1, priority=5, collaborators=[])
            t2 = Task(title="T2", description="D2",
                      deadline=datetime.utcnow() + timedelta(days=7),
                      status="ongoing", owner=self.staff1_id,
                      project_id=pid1, priority=5, collaborators=[])
            t3 = Task(title="T3", description="D3",
                      deadline=datetime.utcnow() + timedelta(days=7),
                      status="done", owner=self.staff1_id,
                      project_id=pid1, priority=5, collaborators=[])
            t4 = Task(title="T4", description="D4",
                      deadline=datetime.utcnow() + timedelta(days=7),
                      status="done", owner=self.staff1_id,
                      project_id=pid2, priority=5, collaborators=[])
            db.session.add_all([t1, t2, t3, t4]); db.session.commit()

        res = self.client.get("/projects")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()

        p1_data = next(p for p in data if p["name"] == "Counts P1")
        p2_data = next(p for p in data if p["name"] == "Counts P2")

        self.assertEqual(p1_data["tasksTotal"], 3)
        self.assertEqual(p1_data["tasksDone"], 2)
        self.assertEqual(p2_data["tasksTotal"], 1)
        self.assertEqual(p2_data["tasksDone"], 1)

        # Verify persisted in DB
        with self.app.app_context():
            p1_row = Project.query.get(pid1)
            p2_row = Project.query.get(pid2)
            self.assertEqual(p1_row.tasks_total, 3)
            self.assertEqual(p1_row.tasks_done, 2)
            self.assertEqual(p2_row.tasks_total, 1)
            self.assertEqual(p2_row.tasks_done, 1)

    def test_task_counts_persist_commit_failure_returns_counts(self):
        """
        If persisting counts fails, the endpoint should still return computed counts.
        """
        from models.task import Task
        from unittest.mock import patch

        with self.app.app_context():
            p = Project(name="Persist Fail P", owner="O", owner_id=self.staff1_id)
            db.session.add(p); db.session.commit()
            pid = p.id
            # 2 tasks, 1 done
            t1 = Task(title="T1", description="D1",
                      deadline=datetime.utcnow() + timedelta(days=7),
                      status="done", owner=self.staff1_id,
                      project_id=pid, priority=5, collaborators=[])
            t2 = Task(title="T2", description="D2",
                      deadline=datetime.utcnow() + timedelta(days=7),
                      status="ongoing", owner=self.staff1_id,
                      project_id=pid, priority=5, collaborators=[])
            db.session.add_all([t1, t2]); db.session.commit()

        # Mock commit to fail during GET
        with patch("projects.app.db.session.commit", side_effect=Exception("commit failed")):
            res = self.client.get("/projects")
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            p_data = next(x for x in data if x["name"] == "Persist Fail P")
            self.assertEqual(p_data["tasksTotal"], 2)
            self.assertEqual(p_data["tasksDone"], 1)

    @patch('projects.app.Task')
    def test_list_projects_with_task_counts(self, mock_task_class):
        """Test that project listing includes task counts from tasks service"""
        # Create a test project
        with self.app.app_context():
            project = Project(
                name="Project with Tasks",
                owner="John Doe",
                owner_id=self.staff1_id
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
                owner_id=self.staff1_id
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
                "id", "name", "owner", "ownerId",
                "tasksDone", "tasksTotal", "dueDate", "updatedAt",
                "memberIds", "memberNames"
            }
            self.assertEqual(set(result.keys()), expected_keys)
            
            # Verify values
            self.assertEqual(result["name"], "Test Project")
            self.assertEqual(result["owner"], "John Doe")
            self.assertEqual(result["ownerId"], self.staff1_id)
            # status removed from API
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
        
        # Should still succeed; owner is auto-added as sole member
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data["memberIds"], [self.staff1_id])
        self.assertEqual(data["memberNames"], ["John Doe"])

    def test_create_project_malformed_json(self):
        """Test creating project with malformed JSON"""
        response = self.client.post(
            "/projects", 
            data="invalid json",
            content_type="application/json"
        )
        
        # Should handle gracefully
        self.assertIn(response.status_code, [400, 500])

    def test_create_project_missing_owner_id(self):
        """Should reject create when ownerId is missing"""
        payload = {
            "name": "No OwnerId Project",
            "owner": "Someone"
        }
        response = self.client.post("/projects", json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("ownerId is required", data.get("error", ""))

    def test_list_projects_large_dataset(self):
        """Test listing projects with many projects"""
        with self.app.app_context():
            # Create many projects
            projects = []
            for i in range(50):
                project = Project(
                    name=f"Project {i}",
                    owner=f"Owner {i}",
                    owner_id=self.staff1_id
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

    # ----------------------------------------------------------------------
    # Test Update Project (owner-only)
    # ----------------------------------------------------------------------

    def test_update_project_due_date_owner_success(self):
        with self.app.app_context():
            project = Project(name="P", owner="Owner", owner_id=self.staff1_id)
            db.session.add(project); db.session.commit()
            pid = project.id

        with self.client.session_transaction() as sess:
            sess["employee_id"] = self.staff1_id

        new_due = (datetime.utcnow() + timedelta(days=10)).isoformat() + "Z"
        res = self.client.put(f"/projects/{pid}", json={"dueDate": new_due})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["id"], pid)
        self.assertIsNotNone(data["dueDate"])
        self.assertIn("T", data["dueDate"])  # ISO
        self.assertTrue(data["dueDate"].endswith("Z"))

        with self.app.app_context():
            p = Project.query.get(pid)
            self.assertIsNotNone(p.due_date)

    def test_update_project_due_date_unauthorized(self):
        with self.app.app_context():
            project = Project(name="P", owner="Owner", owner_id=self.staff1_id)
            db.session.add(project); db.session.commit()
            pid = project.id

        # Ensure no session carries over
        with self.client.session_transaction() as sess:
            sess.clear()

        res = self.client.put(f"/projects/{pid}", json={"dueDate": (datetime.utcnow().isoformat() + "Z")})
        self.assertEqual(res.status_code, 401)

    def test_update_project_due_date_forbidden(self):
        with self.app.app_context():
            project = Project(name="P", owner="Owner", owner_id=self.staff1_id)
            db.session.add(project); db.session.commit()
            pid = project.id

        with self.client.session_transaction() as sess:
            sess["employee_id"] = self.staff2_id

        res = self.client.put(f"/projects/{pid}", json={"dueDate": (datetime.utcnow().isoformat() + "Z")})
        self.assertEqual(res.status_code, 403)

    # ----------------------------------------------------------------------
    # Test Members Update Semantics
    # ----------------------------------------------------------------------

    def test_update_members_add_valid_dedupe_and_ignore_nonexistent(self):
        with self.app.app_context():
            project = Project(name="P", owner="Owner", owner_id=self.staff1_id)
            db.session.add(project); db.session.commit()
            pid = project.id

        with self.client.session_transaction() as sess:
            sess["employee_id"] = self.staff1_id  # owner

        res = self.client.put(f"/projects/{pid}", json={"add": [self.staff1_id, self.staff1_id, self.staff2_id, 9999]})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(set(data["memberIds"]), {self.staff1_id, self.staff2_id})

    def test_update_members_remove_allowed_when_not_involved(self):
        with self.app.app_context():
            project = Project(name="P", owner="Owner", owner_id=self.staff1_id)
            db.session.add(project); db.session.commit()
            pid = project.id
            owner = Staff.query.get(self.staff1_id)
            s2 = Staff.query.get(self.staff2_id)
            project.members.append(owner)
            project.members.append(s2)
            db.session.commit()

        with self.client.session_transaction() as sess:
            sess["employee_id"] = self.staff1_id

        res = self.client.put(f"/projects/{pid}", json={"remove": [self.staff2_id]})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(set(data["memberIds"]), {self.staff1_id})

    def test_update_members_remove_blocked_when_involved(self):
        with self.app.app_context():
            project = Project(name="P", owner="Owner", owner_id=self.staff1_id)
            db.session.add(project); db.session.commit()
            pid = project.id
            s1 = Staff.query.get(self.staff1_id)
            s2 = Staff.query.get(self.staff2_id)
            project.members.append(s1)
            project.members.append(s2)
            db.session.commit()

            # Create a task in this project with staff2 as owner (involved)
            from models.task import Task
            t = Task(title="T", description="D",
                     deadline=datetime.utcnow() + timedelta(days=7),
                     status="ongoing", owner=self.staff2_id,
                     project_id=pid, priority=5, collaborators=[])
            db.session.add(t); db.session.commit()

        with self.client.session_transaction() as sess:
            sess["employee_id"] = self.staff1_id

        res = self.client.put(f"/projects/{pid}", json={"remove": [self.staff2_id]})
        self.assertEqual(res.status_code, 400)
        self.assertIn("unable to remove member", res.get_json().get("error", "").lower())

    def test_update_members_cannot_remove_owner(self):
        with self.app.app_context():
            project = Project(name="P", owner="Owner", owner_id=self.staff1_id)
            db.session.add(project); db.session.commit()
            pid = project.id

        with self.client.session_transaction() as sess:
            sess["employee_id"] = self.staff1_id

        res = self.client.put(f"/projects/{pid}", json={"remove": [self.staff1_id]})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn(self.staff1_id, data["memberIds"])


if __name__ == "__main__":
    unittest.main()
