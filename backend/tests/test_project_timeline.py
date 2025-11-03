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
            # Explicitly clean up the association table first to avoid constraint issues
            db.session.execute(db.text("DELETE FROM task_collaborators"))
            Task.query.delete()
            db.session.commit()
    
    def tearDown(self):
        """Clean up after each test"""
        with self.app.app_context():
            # Explicitly clean up the association table first to avoid constraint issues
            db.session.execute(db.text("DELETE FROM task_collaborators"))
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
            # Staff's own task (should be visible)
            own_task = Task(
                title="My Task",
                description="My task description",
                deadline=datetime.now(timezone.utc) + timedelta(days=5),
                status="ongoing",
                owner=2,  # Staff owns this
                collaborators=[],  # Will add after creation
                priority=1,
                project_id=1
            )
            
            # Manager's task (should NOT be visible to staff)
            manager_task = Task(
                title="Manager Task",
                description="Manager task description",
                deadline=datetime.now(timezone.utc) + timedelta(days=10),
                status="ongoing",
                owner=1,  # Manager owns this
                collaborators=[],  # Will add after creation
                priority=1,
                project_id=1
            )
            
            db.session.add_all([own_task, manager_task])
            db.session.flush()  # Flush to get task IDs but don't commit yet
            
            # Add collaborators using relationship after flush
            own_task.collaborators.append(self.staff1)
            manager_task.collaborators.append(self.manager)
            
            db.session.commit()
            
            # Verify manager_task does NOT have staff as collaborator
            manager_collab_ids = [c.employee_id for c in manager_task.collaborators.all()]
            self.assertNotIn(2, manager_collab_ids, "Staff (id=2) should not be a collaborator of manager's task")
        
        response = self.client.get('/projects/1/timeline')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        # Should only see own task (owner=2), not manager's task
        task_titles = [t['title'] for t in data['tasks']]
        self.assertEqual(len(data['tasks']), 1, f"Expected 1 task but got {len(data['tasks'])}: {task_titles}")
        self.assertEqual(data['tasks'][0]['owner'], 2)
        self.assertIn('My Task', task_titles)
        self.assertNotIn('Manager Task', task_titles)
    
    def test_timeline_staff_access_collaboration(self):
        """Test that staff can see tasks they collaborate on"""
        self.login_as(2, 'staff', 'IT')
        
        with self.app.app_context():
            # Create task owned by manager, add collaborators after creation
            task = Task(
                title="Collaboration Task",
                description="Task description",
                deadline=datetime.now(timezone.utc) + timedelta(days=7),
                status="ongoing",
                owner=1,  # Manager owns
                collaborators=[],  # Will add after creation
                priority=1,
                project_id=1
            )
            db.session.add(task)
            db.session.flush()  # Flush to get task_id but don't commit yet
            
            # Add collaborators using relationship after flush to avoid constraint issues
            task.collaborators.append(self.manager)
            task.collaborators.append(self.staff1)
            
            db.session.commit()
            
            # Verify staff is a collaborator
            collaborator_ids = [c.employee_id for c in task.collaborators.all()]
            self.assertIn(2, collaborator_ids, "Staff (id=2) should be a collaborator")
        
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

    # ----------------------------------------------------------------------
    # Test Personal Timeline (GET /tasks endpoint)
    # ----------------------------------------------------------------------
    
    def test_staff_personal_timeline_my_tasks(self):
        """Test that staff can see their own tasks in personal timeline view (User Story 4)"""
        self.login_as(2, 'staff', 'IT')
        
        with self.client.session_transaction() as sess:
            sess['team'] = 'A'  # Required for /tasks endpoint
        
        with self.app.app_context():
            # Create tasks: one owned by staff, one owned by manager
            my_task = Task(
                title="My Personal Task",
                description="My own task",
                deadline=datetime.now(timezone.utc) + timedelta(days=5),
                status="ongoing",
                owner=2,  # Staff owns this
                collaborators=[self.staff1],  # Owner must be in collaborators for top_level_tasks_for to work
                priority=3,
                project_id=None  # Personal task (no project)
            )
            
            other_task = Task(
                title="Other Person's Task",
                description="Not my task",
                deadline=datetime.now(timezone.utc) + timedelta(days=7),
                status="ongoing",
                owner=1,  # Manager owns this
                collaborators=[self.manager],  # Manager is in collaborators, staff is not
                priority=2,
                project_id=None
            )
            
            db.session.add_all([my_task, other_task])
            db.session.commit()
        
        response = self.client.get('/tasks')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        # Should have 'my_tasks' key
        self.assertIn('my_tasks', data)
        # Staff should see at least their own task
        self.assertGreaterEqual(len(data['my_tasks']), 1)
        # Verify task has required fields for timeline view
        if data['my_tasks']:
            task = data['my_tasks'][0]
            self.assertIn('title', task)
            self.assertIn('status', task)
            self.assertIn('deadline', task)
            self.assertIn('owner', task)

    def test_manager_personal_timeline_my_tasks(self):
        """Test that manager can see their own tasks in personal timeline view (User Story 5)"""
        self.login_as(1, 'manager', 'IT')
        
        with self.client.session_transaction() as sess:
            sess['team'] = 'A'  # Required for /tasks endpoint
        
        with self.app.app_context():
            # Create tasks: one owned by manager, one owned by staff
            my_task = Task(
                title="Manager Personal Task",
                description="Manager's own task",
                deadline=datetime.now(timezone.utc) + timedelta(days=3),
                status="ongoing",
                owner=1,  # Manager owns this
                collaborators=[self.manager],  # Manager must be in collaborators
                priority=5,
                project_id=None  # Personal task
            )
            
            staff_task = Task(
                title="Staff Task",
                description="Staff's task",
                deadline=datetime.now(timezone.utc) + timedelta(days=4),
                status="ongoing",
                owner=2,  # Staff owns this
                collaborators=[self.staff1],  # Staff is in collaborators, manager is not
                priority=2,
                project_id=None
            )
            
            db.session.add_all([my_task, staff_task])
            db.session.commit()
        
        response = self.client.get('/tasks')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        # Should have 'my_tasks' key for manager
        self.assertIn('my_tasks', data)
        # Manager should see at least their own task
        self.assertGreaterEqual(len(data['my_tasks']), 1)
        # Verify task has required timeline fields
        if data['my_tasks']:
            task = data['my_tasks'][0]
            required_fields = ['title', 'status', 'deadline', 'owner']
            for field in required_fields:
                self.assertIn(field, task)

    def test_hr_director_personal_timeline_my_tasks(self):
        """Test that HR/Senior Director can see their own tasks in personal timeline view (User Story 6)"""
        self.login_as(4, 'senior manager', 'HR')
        
        with self.client.session_transaction() as sess:
            sess['team'] = 'B'  # Required for /tasks endpoint
        
        with self.app.app_context():
            # Create tasks: one owned by HR user
            my_task = Task(
                title="HR Personal Task",
                description="HR's own task",
                deadline=datetime.now(timezone.utc) + timedelta(days=2),
                status="ongoing",
                owner=4,  # HR user owns this
                collaborators=[self.hr_user],  # HR user must be in collaborators
                priority=4,
                project_id=None  # Personal task
            )
            
            db.session.add(my_task)
            db.session.commit()
        
        response = self.client.get('/tasks')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        # Should have 'my_tasks' key
        self.assertIn('my_tasks', data)
        # HR/Director should see their own tasks
        self.assertGreaterEqual(len(data['my_tasks']), 1)
        # Verify task structure for timeline view
        if data['my_tasks']:
            task = data['my_tasks'][0]
            self.assertIn('title', task)
            self.assertIn('status', task)
            self.assertIn('deadline', task)
            self.assertIn('owner', task)
            # Verify owner matches
            self.assertEqual(task['owner'], 4)

    def test_overdue_tasks_in_project_timeline(self):
        """Test that overdue tasks are returned in project timeline (User Story 7)"""
        self.login_as(1, 'manager', 'IT')
        
        with self.app.app_context():
            # Create tasks: one overdue (past deadline), one not overdue
            base_date = datetime.now(timezone.utc)
            
            overdue_task = Task(
                title="Overdue Task",
                description="This task is overdue",
                deadline=base_date - timedelta(days=2),  # 2 days ago (overdue)
                status="ongoing",  # Not completed, so it's overdue
                owner=1,
                collaborators=[],
                priority=7,
                project_id=1
            )
            
            future_task = Task(
                title="Future Task",
                description="This task is not overdue",
                deadline=base_date + timedelta(days=5),  # 5 days from now
                status="ongoing",
                owner=1,
                collaborators=[],
                priority=3,
                project_id=1
            )
            
            db.session.add_all([overdue_task, future_task])
            db.session.commit()
        
        response = self.client.get('/projects/1/timeline')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        tasks = data['tasks']
        
        # Should return both tasks
        self.assertEqual(len(tasks), 2)
        
        # Find overdue task
        overdue_found = False
        for task in tasks:
            if task['title'] == 'Overdue Task':
                overdue_found = True
                # Verify task has due_date field (frontend can check if it's overdue)
                self.assertIsNotNone(task['due_date'])
                # Verify task is still ongoing (not done, so it's truly overdue)
                self.assertEqual(task['status'], 'ongoing')
                # Verify due_date is in the past (check by parsing ISO string)
                due_date_obj = datetime.fromisoformat(task['due_date'].replace('Z', '+00:00'))
                self.assertLess(due_date_obj.replace(tzinfo=timezone.utc), datetime.now(timezone.utc))
        
        self.assertTrue(overdue_found, "Overdue task should be present in timeline response")


if __name__ == '__main__':
    unittest.main()
