# backend/tests/test_project_timeline.py
import unittest
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

# Set testing environment
os.environ['TESTING'] = 'true'

from tasks.task import app
from models.extensions import db
from models.task import Task
from models.staff import Staff
from models.project import Project


class TestProjectTimelineAPI(unittest.TestCase):
    """Test cases for project timeline API endpoint"""
    
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
            cls.manager = Staff(
                employee_id=1,
                employee_name="Manager User",
                email="manager@test.com",
                role="manager",
                department="IT",
                team="A",
                password="test123"
            )
            cls.staff1 = Staff(
                employee_id=2,
                employee_name="Staff User 1",
                email="staff1@test.com",
                role="staff",
                department="IT",
                team="A",
                password="test123"
            )
            cls.staff2 = Staff(
                employee_id=3,
                employee_name="Staff User 2",
                email="staff2@test.com",
                role="staff",
                department="IT",
                team="A",
                password="test123"
            )
            cls.hr_user = Staff(
                employee_id=4,
                employee_name="HR User",
                email="hr@test.com",
                role="senior manager",  # Use senior manager role
                department="HR",
                team="B",
                password="test123"
            )
            
            db.session.add_all([cls.manager, cls.staff1, cls.staff2, cls.hr_user])
            db.session.commit()
            
            # Create test project
            cls.project = Project(
                id=1,
                name="Test Project",
                owner="Manager User",
                owner_id=1,
                tasks_done=0,
                tasks_total=3
            )
            db.session.add(cls.project)
            db.session.commit()
            
            # Ensure project has members from multiple departments for HR visibility tests
            cls.project.members.append(cls.manager)
            cls.project.members.append(cls.staff1)
            cls.project.members.append(cls.staff2)
            cls.project.members.append(cls.hr_user)
            db.session.commit()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        with cls.app.app_context():
            db.drop_all()
    
    def setUp(self):
        """Set up fresh state before each test"""
        with self.app.app_context():
            # Clean up tasks
            Task.query.delete()
            db.session.commit()
    
    def tearDown(self):
        """Clean up after each test"""
        with self.app.app_context():
            Task.query.delete()
            db.session.commit()
    
    def login_as(self, employee_id, role, department="IT"):
        """Helper method to simulate login"""
        with self.client.session_transaction() as sess:
            sess['employee_id'] = employee_id
            sess['role'] = role
            sess['department'] = department
    
    # ----------------------------------------------------------------------
    # Test Authentication & Authorization
    # ----------------------------------------------------------------------
    
    def test_timeline_requires_authentication(self):
        """Test that timeline endpoint requires authentication"""
        # Clear any existing session
        with self.client.session_transaction() as sess:
            sess.clear()
        
        response = self.client.get('/projects/1/timeline')
        self.assertEqual(response.status_code, 401)
        self.assertIn('error', response.get_json())
    
    def test_timeline_manager_access(self):
        """Test that manager can access timeline for their department"""
        self.login_as(1, 'manager', 'IT')
        
        with self.app.app_context():
            # Create tasks for the project
            task1 = Task(
                title="Manager Task",
                description="Task description",
                deadline=datetime.now(timezone.utc) + timedelta(days=7),
                status="ongoing",
                owner=1,
                collaborators=[],
                priority=1,
                project_id=1
            )
            db.session.add(task1)
            db.session.commit()
        
        response = self.client.get('/projects/1/timeline')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertIn('tasks', data)
        self.assertIn('team_members', data)
        self.assertIn('project_id', data)
    
    def test_timeline_staff_access_own_tasks(self):
        """Test that staff can only see their own tasks and collaborations"""
        self.login_as(2, 'staff', 'IT')
        
        with self.app.app_context():
            # Create tasks - one owned by staff, one by manager
            own_task = Task(
                title="My Task",
                description="My task description",
                deadline=datetime.now(timezone.utc) + timedelta(days=5),
                status="ongoing",
                owner=2,  # Staff owns this
                collaborators=[],
                priority=1,
                project_id=1
            )
            
            manager_task = Task(
                title="Manager Task",
                description="Manager task description",
                deadline=datetime.now(timezone.utc) + timedelta(days=10),
                status="ongoing",
                owner=1,  # Manager owns this
                collaborators=[],
                priority=1,
                project_id=1
            )
            
            db.session.add_all([own_task, manager_task])
            db.session.commit()
        
        response = self.client.get('/projects/1/timeline')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        # Should only see own task
        self.assertEqual(len(data['tasks']), 1)
        self.assertEqual(data['tasks'][0]['owner'], 2)
    
    def test_timeline_staff_access_collaboration(self):
        """Test that staff can see tasks they collaborate on"""
        self.login_as(2, 'staff', 'IT')
        
        with self.app.app_context():
            # Create task owned by manager but with staff as collaborator
            task = Task(
                title="Collaboration Task",
                description="Task description",
                deadline=datetime.now(timezone.utc) + timedelta(days=7),
                status="ongoing",
                owner=1,  # Manager owns
                collaborators=[],
                priority=1,
                project_id=1
            )
            db.session.add(task)
            db.session.commit()
            
            # Add staff as collaborator
            task.collaborators.append(self.staff1)
            db.session.commit()
        
        response = self.client.get('/projects/1/timeline')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        # Should see the collaboration task
        self.assertEqual(len(data['tasks']), 1)
        self.assertIn(2, data['tasks'][0]['collaborators'])
    
    def test_timeline_hr_access_all_tasks(self):
        """Test that HR can see all tasks across departments"""
        self.login_as(4, 'senior manager', 'HR')  # Use 'senior manager' role
        
        with self.app.app_context():
            # Create tasks from different departments
            it_task = Task(
                title="IT Task",
                description="IT task description",
                deadline=datetime.now(timezone.utc) + timedelta(days=5),
                status="ongoing",
                owner=2,  # IT staff
                collaborators=[],
                priority=1,
                project_id=1
            )
            
            db.session.add(it_task)
            db.session.commit()
        
        response = self.client.get('/projects/1/timeline')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        # HR should see all tasks
        self.assertEqual(len(data['tasks']), 1)
        # HR should see all team members
        self.assertGreater(len(data['team_members']), 1)
    
    # ----------------------------------------------------------------------
    # Test Data Structure & Format
    # ----------------------------------------------------------------------
    
    def test_timeline_response_structure(self):
        """Test that timeline response has correct structure"""
        self.login_as(1, 'manager', 'IT')
        
        with self.app.app_context():
            # Create a task
            task = Task(
                title="Test Task",
                description="Test description",
                deadline=datetime.now(timezone.utc) + timedelta(days=3),
                status="completed",
                owner=1,
                collaborators=[],
                priority=2,
                project_id=1
            )
            db.session.add(task)
            db.session.commit()
        
        response = self.client.get('/projects/1/timeline')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        
        # Check required fields
        required_fields = ['project_id', 'tasks', 'team_members', 'project_date_range']
        for field in required_fields:
            self.assertIn(field, data)
        
        # Check task structure
        if data['tasks']:
            task = data['tasks'][0]
            task_fields = ['id', 'title', 'description', 'status', 'priority', 
                          'due_date', 'owner', 'collaborators', 'project_id']
            for field in task_fields:
                self.assertIn(field, task)
        
        # Check team member structure
        if data['team_members']:
            member = data['team_members'][0]
            member_fields = ['employee_id', 'employee_name', 'role', 'department', 'team']
            for field in member_fields:
                self.assertIn(field, member)
    
    def test_timeline_empty_project(self):
        """Test timeline for project with no tasks"""
        self.login_as(1, 'manager', 'IT')
        
        response = self.client.get('/projects/1/timeline')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertEqual(data['project_id'], 1)
        self.assertEqual(data['tasks'], [])
        self.assertIsInstance(data['team_members'], list)
    
    def test_timeline_date_formatting(self):
        """Test that dates are properly formatted in ISO format"""
        self.login_as(1, 'manager', 'IT')
        
        with self.app.app_context():
            due_date = datetime.now(timezone.utc) + timedelta(days=5)
            task = Task(
                title="Date Test Task",
                description="Testing date formatting",
                deadline=due_date,
                status="ongoing",
                owner=1,
                collaborators=[],
                priority=1,
                project_id=1
            )
            db.session.add(task)
            db.session.commit()
        
        response = self.client.get('/projects/1/timeline')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        task_data = data['tasks'][0]
        
        # Check date format
        self.assertIsNotNone(task_data['due_date'])
        self.assertRegex(task_data['due_date'], r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}')
    
    # ----------------------------------------------------------------------
    # Test Project Date Range Calculation
    # ----------------------------------------------------------------------
    
    def test_project_date_range_calculation(self):
        """Test that project date range is calculated correctly"""
        self.login_as(1, 'manager', 'IT')
        
        with self.app.app_context():
            # Create tasks with different due dates
            base_date = datetime.now(timezone.utc)
            
            task1 = Task(
                title="Early Task",
                description="Early task",
                deadline=base_date + timedelta(days=1),
                status="ongoing",
                owner=1,
                collaborators=[],
                priority=1,
                project_id=1
            )
            
            task2 = Task(
                title="Late Task",
                description="Late task",
                deadline=base_date + timedelta(days=10),
                status="ongoing",
                owner=1,
                collaborators=[],
                priority=1,
                project_id=1
            )
            
            task3 = Task(
                title="Middle Task",
                description="Middle task",
                deadline=base_date + timedelta(days=5),
                status="ongoing",
                owner=1,
                collaborators=[],
                priority=1,
                project_id=1
            )
            
            db.session.add_all([task1, task2, task3])
            db.session.commit()
            
            # Store the dates before the session closes
            task1_date = task1.deadline.isoformat()
            task2_date = task2.deadline.isoformat()
        
        response = self.client.get('/projects/1/timeline')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        date_range = data['project_date_range']
        
        self.assertIsNotNone(date_range)
        self.assertIn('start_date', date_range)
        self.assertIn('end_date', date_range)
        
        # Start date should be earliest, end date should be latest
        self.assertEqual(date_range['start_date'], task1_date)
        self.assertEqual(date_range['end_date'], task2_date)
    
    def test_project_date_range_no_due_dates(self):
        """Test project date range when tasks have no due dates"""
        self.login_as(1, 'manager', 'IT')
        
        with self.app.app_context():
            # Create task without due date
            task = Task(
                title="No Due Date Task",
                description="Task without due date",
                deadline=None,
                status="ongoing",
                owner=1,
                collaborators=[],
                priority=1,
                project_id=1
            )
            db.session.add(task)
            db.session.commit()
        
        response = self.client.get('/projects/1/timeline')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        # Should be None when no tasks have due dates
        self.assertIsNone(data['project_date_range'])
    
    # ----------------------------------------------------------------------
    # Test Error Handling
    # ----------------------------------------------------------------------
    
    def test_timeline_nonexistent_project(self):
        """Test timeline for non-existent project"""
        self.login_as(1, 'manager', 'IT')
        
        response = self.client.get('/projects/999/timeline')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertEqual(data['project_id'], 999)
        self.assertEqual(data['tasks'], [])
    
    def test_timeline_database_error_handling(self):
        """Test that database errors are handled gracefully"""
        self.login_as(1, 'manager', 'IT')
        
        # Mock database error
        with self.app.app_context():
            with patch('models.task.Task.query') as mock_query:
                mock_query.filter_by.side_effect = Exception("Database error")
                
                response = self.client.get('/projects/1/timeline')
                self.assertEqual(response.status_code, 500)
                
                data = response.get_json()
                self.assertIn('error', data)
    
    # ----------------------------------------------------------------------
    # Test Team Member Filtering
    # ----------------------------------------------------------------------
    
    def test_team_members_manager_department(self):
        """Test that manager sees only department team members"""
        self.login_as(1, 'manager', 'IT')
        
        response = self.client.get('/projects/1/timeline')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        team_members = data['team_members']
        
        # Should only see IT department members
        for member in team_members:
            self.assertEqual(member['department'], 'IT')
    
    def test_team_members_hr_all_departments(self):
        """Test that HR sees all team members"""
        self.login_as(4, 'senior manager', 'HR')  # Use 'senior manager' role
        
        with self.app.app_context():
            # Create a task so the timeline endpoint has data to work with
            task = Task(
                title="Test Task",
                description="Test description",
                deadline=datetime.now(timezone.utc) + timedelta(days=5),
                status="ongoing",
                owner=1,
                collaborators=[],
                priority=1,
                project_id=1
            )
            db.session.add(task)
            db.session.commit()
        
        response = self.client.get('/projects/1/timeline')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        team_members = data['team_members']
        
        # Should see members from multiple departments (IT and HR)
        departments = set(member['department'] for member in team_members)
        self.assertGreater(len(departments), 1)
    
    def test_team_members_staff_department(self):
        """Test that staff sees department team members for context"""
        self.login_as(2, 'staff', 'IT')
        
        response = self.client.get('/projects/1/timeline')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        team_members = data['team_members']
        
        # Should see IT department members
        for member in team_members:
            self.assertEqual(member['department'], 'IT')


if __name__ == '__main__':
    unittest.main()
