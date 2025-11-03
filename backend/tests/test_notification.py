"""
Unit Tests for Notification Microservice Requirements

This test suite validates all 6 requirements for the notification system:
1. Approaching Deadlines and Customization
2. Overdue Tasks
3. New Comments on Task
4. User Mentions
5. Subtask Notifications
6. Task Updates

Test Framework: unittest
"""
import unittest
import sys
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
import json

# CRITICAL: Set TESTING environment variable BEFORE importing app
# This ensures the app uses SQLite in-memory database instead of MySQL
os.environ['TESTING'] = 'True'

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from notifications.app import app, db, _within_day, _send_deadline_reminders
from models.notification import Notification, NotificationPreferences, DeadlineNotificationLog
from models.staff import Staff


class TestRequirement1_ApproachingDeadlines(unittest.TestCase):
    """
    REQUIREMENT 1: Send alerts for approaching deadlines
    - Default reminder days: 7, 3, 1 days before deadline
    - Users can customize and add to those number of days
    """
    
    def setUp(self):
        """Set up test environment before each test"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        self.app = app
        self.client = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()
        
        # Drop and recreate all tables for clean test environment
        db.drop_all()
        db.create_all()
        
        # Create test staff with password
        self.test_staff = Staff(
            employee_id=100,
            employee_name="Test User",
            email="test@example.com",
            password="hashed_password_123",  # Added password
            role="staff",
            department="IT",
            team="Development"
        )
        db.session.add(self.test_staff)
        db.session.commit()
    
    def tearDown(self):
        """Clean up after each test"""
        db.session.remove()
        db.drop_all()
        self.ctx.pop()
    
    def test_default_reminder_days_7_3_1(self):
        """Test that default reminder days are 7, 3, 1"""
        # Get or create default preferences
        response = self.client.get('/api/preferences', headers={
            'X-Employee-Id': '100'
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        # Verify default reminder days
        self.assertEqual(data['deadline_reminder_days'], '7,3,1')
        self.assertTrue(data['deadline_reminders'])
    
    def test_customize_reminder_days(self):
        """Test that users can customize reminder days"""
        # Update preferences with custom days
        response = self.client.put('/api/preferences',
            headers={'X-Employee-Id': '100'},
            json={
                'deadline_reminder_days': '14,10,7,3,1'
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        # Verify custom reminder days were saved
        self.assertEqual(data['deadline_reminder_days'], '14,10,7,3,1')
    
    def test_add_to_default_reminder_days(self):
        """Test that users can add additional reminder days"""
        # Start with default
        self.client.get('/api/preferences', headers={'X-Employee-Id': '100'})
        
        # Add 14 days to the default 7,3,1
        response = self.client.put('/api/preferences',
            headers={'X-Employee-Id': '100'},
            json={
                'deadline_reminder_days': '14,7,3,1'
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        # Verify the addition
        self.assertIn('14', data['deadline_reminder_days'])
        self.assertIn('7', data['deadline_reminder_days'])
        self.assertIn('3', data['deadline_reminder_days'])
        self.assertIn('1', data['deadline_reminder_days'])
    
    @patch('notifications.app.requests.get')
    def test_deadline_notification_7_days(self, mock_get):
        """Test deadline notification is sent 7 days before deadline"""
        # Mock task service response
        deadline_7_days = datetime.now(timezone.utc) + timedelta(days=7)
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = {
            'tasks': [{
                'task_id': 1,
                'title': 'Test Task',
                'deadline': deadline_7_days.isoformat(),
                'status': 'ongoing',
                'owner': 100,
                'collaborators': [100],
                'parent_id': None
            }]
        }
        
        # Run deadline reminder check
        _send_deadline_reminders()
        
        # Verify notification was created
        notifications = Notification.query.filter_by(staff_id=100).all()
        deadline_notifs = [n for n in notifications if 'deadline_7_days' in n.type]
        
        self.assertGreater(len(deadline_notifs), 0)
        self.assertIn('Deadline in 7 days', deadline_notifs[0].title)
    
    @patch('notifications.app.requests.get')
    def test_deadline_notification_3_days(self, mock_get):
        """Test deadline notification is sent 3 days before deadline"""
        deadline_3_days = datetime.now(timezone.utc) + timedelta(days=3)
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = {
            'tasks': [{
                'task_id': 2,
                'title': 'Test Task 3 Days',
                'deadline': deadline_3_days.isoformat(),
                'status': 'ongoing',
                'owner': 100,
                'collaborators': [100],
                'parent_id': None
            }]
        }
        
        _send_deadline_reminders()
        
        notifications = Notification.query.filter_by(staff_id=100).all()
        deadline_notifs = [n for n in notifications if 'deadline_3_days' in n.type]
        
        self.assertGreater(len(deadline_notifs), 0)
        self.assertIn('Deadline in 3 days', deadline_notifs[0].title)
    
    @patch('notifications.app.requests.get')
    def test_deadline_notification_1_day(self, mock_get):
        """Test deadline notification is sent 1 day before deadline"""
        deadline_1_day = datetime.now(timezone.utc) + timedelta(days=1)
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = {
            'tasks': [{
                'task_id': 3,
                'title': 'Test Task 1 Day',
                'deadline': deadline_1_day.isoformat(),
                'status': 'ongoing',
                'owner': 100,
                'collaborators': [100],
                'parent_id': None
            }]
        }
        
        _send_deadline_reminders()
        
        notifications = Notification.query.filter_by(staff_id=100).all()
        deadline_notifs = [n for n in notifications if 'deadline_1_day' in n.type]
        
        self.assertGreater(len(deadline_notifs), 0)
        self.assertIn('Deadline in 1 day', deadline_notifs[0].title)
    
    @patch('notifications.app.requests.get')
    def test_custom_deadline_notification_14_days(self, mock_get):
        """Test custom deadline notification (14 days)"""
        # Set custom preference
        self.client.put('/api/preferences',
            headers={'X-Employee-Id': '100'},
            json={'deadline_reminder_days': '14,7,3,1'}
        )
        
        deadline_14_days = datetime.now(timezone.utc) + timedelta(days=14)
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = {
            'tasks': [{
                'task_id': 4,
                'title': 'Test Task 14 Days',
                'deadline': deadline_14_days.isoformat(),
                'status': 'ongoing',
                'owner': 100,
                'collaborators': [100],
                'parent_id': None
            }]
        }
        
        _send_deadline_reminders()
        
        notifications = Notification.query.filter_by(staff_id=100).all()
        deadline_notifs = [n for n in notifications if 'deadline_14_days' in n.type]
        
        self.assertGreater(len(deadline_notifs), 0)
        self.assertIn('Deadline in 14 days', deadline_notifs[0].title)
    
    def test_within_day_calculation_accuracy(self):
        """Test that _within_day function calculates correctly"""
        # Test 7 days before deadline
        deadline = datetime.now(timezone.utc) + timedelta(days=7)
        self.assertTrue(_within_day(deadline, 7))
        
        # Test 3 days before deadline
        deadline = datetime.now(timezone.utc) + timedelta(days=3)
        self.assertTrue(_within_day(deadline, 3))
        
        # Test 1 day before deadline
        deadline = datetime.now(timezone.utc) + timedelta(days=1)
        self.assertTrue(_within_day(deadline, 1))
        
        # Test not within day
        deadline = datetime.now(timezone.utc) + timedelta(days=7)
        self.assertFalse(_within_day(deadline, 3))


class TestRequirement2_OverdueTasks(unittest.TestCase):
    """
    REQUIREMENT 2: Notify owner and collaborators when task is overdue
    """
    
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        self.app = app
        self.client = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()
        
        # Drop and recreate all tables for clean test environment
        db.drop_all()
        db.create_all()
        
        # Create test staff members with passwords
        self.owner = Staff(employee_id=101, employee_name="Owner", email="owner@test.com", 
                          password="password123", role="manager", department="IT", team="Dev")
        self.collaborator = Staff(employee_id=102, employee_name="Collaborator", 
                                 email="collab@test.com", password="password123", 
                                 role="staff", department="IT", team="Dev")
        db.session.add(self.owner)
        db.session.add(self.collaborator)
        db.session.commit()
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()
    
    @patch('notifications.app.requests.get')
    def test_overdue_task_notification_sent(self, mock_get):
        """Test that overdue notification is sent for overdue tasks"""
        # Task with deadline in the past
        past_deadline = datetime.now(timezone.utc) - timedelta(days=2)
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = {
            'tasks': [{
                'task_id': 10,
                'title': 'Overdue Task',
                'deadline': past_deadline.isoformat(),
                'status': 'ongoing',
                'owner': 101,
                'collaborators': [101, 102],
                'parent_id': None
            }]
        }
        
        _send_deadline_reminders()
        
        # Verify notifications for both owner and collaborator
        owner_notifs = Notification.query.filter_by(staff_id=101, type='overdue_task').all()
        collab_notifs = Notification.query.filter_by(staff_id=102, type='overdue_task').all()
        
        self.assertGreater(len(owner_notifs), 0)
        self.assertGreater(len(collab_notifs), 0)
        self.assertIn('overdue', owner_notifs[0].title.lower())
    
    @patch('notifications.app.requests.get')
    def test_no_overdue_notification_for_completed_tasks(self, mock_get):
        """Test that overdue notifications are NOT sent for completed tasks"""
        past_deadline = datetime.now(timezone.utc) - timedelta(days=2)
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = {
            'tasks': [{
                'task_id': 11,
                'title': 'Completed Task',
                'deadline': past_deadline.isoformat(),
                'status': 'done',  # Task is completed
                'owner': 101,
                'collaborators': [101],
                'parent_id': None
            }]
        }
        
        _send_deadline_reminders()
        
        # Should not create overdue notifications
        notifs = Notification.query.filter_by(staff_id=101, type='overdue_task').all()
        self.assertEqual(len(notifs), 0)
    
    @patch('notifications.app.requests.get')
    def test_overdue_notification_deduplication(self, mock_get):
        """Test that duplicate overdue notifications are prevented"""
        past_deadline = datetime.now(timezone.utc) - timedelta(days=2)
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = {
            'tasks': [{
                'task_id': 12,
                'title': 'Overdue Task',
                'deadline': past_deadline.isoformat(),
                'status': 'ongoing',
                'owner': 101,
                'collaborators': [101],
                'parent_id': None
            }]
        }
        
        # Run twice
        _send_deadline_reminders()
        _send_deadline_reminders()
        
        # Should only have one notification
        notifs = Notification.query.filter_by(staff_id=101, type='overdue_task', related_task_id=12).all()
        self.assertEqual(len(notifs), 1)


class TestRequirement3_NewComments(unittest.TestCase):
    """
    REQUIREMENT 3: Notify owner and collaborators of new comments on task
    """
    
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        self.app = app
        self.client = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()
        
        # Drop and recreate all tables for clean test environment
        db.drop_all()
        db.create_all()
        
        self.staff1 = Staff(employee_id=201, employee_name="User1", email="u1@test.com",
                           password="password123", role="staff", department="IT", team="Dev")
        self.staff2 = Staff(employee_id=202, employee_name="User2", email="u2@test.com",
                           password="password123", role="staff", department="IT", team="Dev")
        db.session.add(self.staff1)
        db.session.add(self.staff2)
        db.session.commit()
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()
    
    def test_comment_added_notification_endpoint(self):
        """Test that comment-added endpoint creates notifications"""
        response = self.client.post('/api/events/comment-added',
            json={
                'staff_id': 201,
                'action': 'added',
                'title': 'Comments updated: Test Task',
                'message': 'New comment added by User2: This is a test comment',
                'related_task_id': 20,
                'related_comment_id': 100,
                'actor_name': 'User2'
            }
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify notification was created
        notif = Notification.query.filter_by(staff_id=201).first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.type, 'comments_updated')
        self.assertIn('Comments updated', notif.title)
        self.assertEqual(notif.related_task_id, 20)
    
    def test_comment_updated_notification_endpoint(self):
        """Test that comment-updated endpoint creates notifications"""
        response = self.client.post('/api/events/comment-updated',
            json={
                'staff_id': 202,
                'action': 'updated',
                'title': 'Comments updated: Test Task',
                'message': 'Comment updated by User1: Updated comment',
                'related_task_id': 21,
                'related_comment_id': 101,
                'actor_name': 'User1'
            }
        )
        
        self.assertEqual(response.status_code, 200)
        
        notif = Notification.query.filter_by(staff_id=202).first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.type, 'comments_updated')
    
    def test_comment_notification_includes_actor_name(self):
        """Test that comment notifications include actor name in message"""
        response = self.client.post('/api/events/comment-added',
            json={
                'staff_id': 201,
                'title': 'Comments updated: Task',
                'message': 'New comment added by John Smith: Great work!',
                'related_task_id': 22,
                'actor_name': 'John Smith'
            }
        )
        
        self.assertEqual(response.status_code, 200)
        
        notif = Notification.query.filter_by(staff_id=201).first()
        self.assertIn('John Smith', notif.message)
    
    def test_multiple_collaborators_receive_comment_notification(self):
        """Test that all collaborators receive comment notifications"""
        # Send to multiple users
        for staff_id in [201, 202]:
            self.client.post('/api/events/comment-added',
                json={
                    'staff_id': staff_id,
                    'title': 'Comments updated: Team Task',
                    'message': 'New comment added',
                    'related_task_id': 23,
                    'actor_name': 'TeamMember'
                }
            )
        
        # Verify all received notifications
        notifs_user1 = Notification.query.filter_by(staff_id=201).all()
        notifs_user2 = Notification.query.filter_by(staff_id=202).all()
        
        self.assertGreater(len(notifs_user1), 0)
        self.assertGreater(len(notifs_user2), 0)


class TestRequirement4_UserMentions(unittest.TestCase):
    """
    REQUIREMENT 4: Notify users when mentioned by teammates
    """
    
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        self.app = app
        self.client = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()
        
        # Drop and recreate all tables for clean test environment
        db.drop_all()
        db.create_all()
        
        self.mentioned_user = Staff(employee_id=301, employee_name="Mentioned User",
                                   email="mentioned@test.com", password="password123",
                                   role="staff", department="IT", team="Dev")
        db.session.add(self.mentioned_user)
        db.session.commit()
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()
    
    def test_mention_notification_created(self):
        """Test that mention notifications are created"""
        response = self.client.post('/api/events/mention',
            json={
                'staff_id': 301,
                'title': 'You were mentioned in: Test Task',
                'message': 'John mentioned you in a comment: @MentionedUser please review',
                'related_task_id': 30,
                'related_comment_id': 200
            }
        )
        
        self.assertEqual(response.status_code, 200)
        
        notif = Notification.query.filter_by(staff_id=301, type='mention').first()
        self.assertIsNotNone(notif)
        self.assertIn('mentioned', notif.title.lower())
    
    def test_mention_notification_has_task_context(self):
        """Test that mention notifications include task context"""
        response = self.client.post('/api/events/mention',
            json={
                'staff_id': 301,
                'title': 'You were mentioned in: Project Planning',
                'message': 'Alice mentioned you: @User can you help?',
                'related_task_id': 31,
                'related_comment_id': 201
            }
        )
        
        self.assertEqual(response.status_code, 200)
        
        notif = Notification.query.filter_by(staff_id=301).first()
        self.assertEqual(notif.related_task_id, 31)
        self.assertEqual(notif.related_comment_id, 201)
    
    def test_mention_notification_requires_all_fields(self):
        """Test that mention endpoint validates required fields"""
        # Missing message
        response = self.client.post('/api/events/mention',
            json={
                'staff_id': 301,
                'title': 'You were mentioned'
                # Missing 'message'
            }
        )
        
        self.assertEqual(response.status_code, 400)


class TestRequirement5_SubtaskNotifications(unittest.TestCase):
    """
    REQUIREMENT 5: Subtasks have their own notifications unique to them, separate from tasks
    """
    
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        self.app = app
        self.client = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()
        
        # Drop and recreate all tables for clean test environment
        db.drop_all()
        db.create_all()
        
        self.staff = Staff(employee_id=401, employee_name="Subtask User",
                          email="subtask@test.com", password="password123",
                          role="staff", department="IT", team="Dev")
        db.session.add(self.staff)
        db.session.commit()
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()
    
    @patch('notifications.app.requests.get')
    def test_subtask_deadline_notification_has_subtask_prefix(self, mock_get):
        """Test that subtask notifications are labeled with 'Subtask' prefix"""
        deadline = datetime.now(timezone.utc) + timedelta(days=7)
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = {
            'tasks': [{
                'task_id': 40,
                'title': 'Subtask Item',
                'deadline': deadline.isoformat(),
                'status': 'ongoing',
                'owner': 401,
                'collaborators': [401],
                'parent_id': 39  # Has parent_id = subtask
            }]
        }
        
        _send_deadline_reminders()
        
        notifs = Notification.query.filter_by(staff_id=401).all()
        self.assertGreater(len(notifs), 0)
        
        # Verify "Subtask" prefix in title
        self.assertIn('Subtask', notifs[0].title)
    
    @patch('notifications.app.requests.get')
    def test_subtask_overdue_notification_separate_from_parent(self, mock_get):
        """Test that subtask overdue notifications are separate from parent task"""
        past_deadline = datetime.now(timezone.utc) - timedelta(days=1)
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = {
            'tasks': [{
                'task_id': 41,
                'title': 'Overdue Subtask',
                'deadline': past_deadline.isoformat(),
                'status': 'ongoing',
                'owner': 401,
                'collaborators': [401],
                'parent_id': 40  # Subtask
            }]
        }
        
        _send_deadline_reminders()
        
        notifs = Notification.query.filter_by(staff_id=401, type='overdue_task').all()
        self.assertGreater(len(notifs), 0)
        self.assertIn('Subtask', notifs[0].title)
    
    @patch('notifications.app.requests.get')
    def test_subtask_and_parent_have_different_notifications(self, mock_get):
        """Test that subtasks and parent tasks generate distinct notifications"""
        deadline = datetime.now(timezone.utc) + timedelta(days=3)
        
        # Parent task
        parent_task = {
            'task_id': 42,
            'title': 'Parent Task',
            'deadline': deadline.isoformat(),
            'status': 'ongoing',
            'owner': 401,
            'collaborators': [401],
            'parent_id': None  # Parent
        }
        
        # Subtask
        subtask = {
            'task_id': 43,
            'title': 'Child Subtask',
            'deadline': deadline.isoformat(),
            'status': 'ongoing',
            'owner': 401,
            'collaborators': [401],
            'parent_id': 42  # Child
        }
        
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = {
            'tasks': [parent_task, subtask]
        }
        
        _send_deadline_reminders()
        
        # Both should create notifications
        notifs = Notification.query.filter_by(staff_id=401).all()
        self.assertGreaterEqual(len(notifs), 2)
        
        # One should have "Subtask" prefix, one should not
        subtask_notifs = [n for n in notifs if 'Subtask' in n.title]
        parent_notifs = [n for n in notifs if 'Subtask' not in n.title]
        
        self.assertGreater(len(subtask_notifs), 0)
        self.assertGreater(len(parent_notifs), 0)


class TestRequirement6_TaskUpdates(unittest.TestCase):
    """
    REQUIREMENT 6: Task updates (name, description, priority, status, due date) 
    must notify owner and collaborators
    """
    
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        self.app = app
        self.client = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()
        
        # Drop and recreate all tables for clean test environment
        db.drop_all()
        db.create_all()
        
        self.owner = Staff(employee_id=501, employee_name="Task Owner",
                          email="owner@test.com", password="password123",
                          role="manager", department="IT", team="Dev")
        self.collaborator = Staff(employee_id=502, employee_name="Collaborator",
                                 email="collab@test.com", password="password123",
                                 role="staff", department="IT", team="Dev")
        db.session.add(self.owner)
        db.session.add(self.collaborator)
        db.session.commit()
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()
    
    @patch('notifications.app.requests.get')
    def test_task_name_change_notification(self, mock_get):
        """Test notification for task name change"""
        # Mock task data
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = {
            'task_id': 50,
            'title': 'Updated Task Name',
            'owner': 501,
            'collaborators': [501, 502]
        }
        
        response = self.client.post('/api/events/task-updated',
            json={
                'task_id': 50,
                'changed_fields': ['title'],
                'actor_id': 501
            }
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify notifications created
        notifs = Notification.query.filter_by(type='name_updated').all()
        self.assertGreater(len(notifs), 0)
        self.assertIn('name updated', notifs[0].title.lower())
    
    @patch('notifications.app.requests.get')
    def test_task_description_change_notification(self, mock_get):
        """Test notification for task description change"""
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = {
            'task_id': 51,
            'title': 'Test Task',
            'owner': 501,
            'collaborators': [501, 502]
        }
        
        response = self.client.post('/api/events/task-updated',
            json={
                'task_id': 51,
                'changed_fields': ['description'],
                'actor_id': 501
            }
        )
        
        self.assertEqual(response.status_code, 200)
        
        notifs = Notification.query.filter_by(type='description_updated').all()
        self.assertGreater(len(notifs), 0)
    
    @patch('notifications.app.requests.get')
    def test_task_priority_change_notification(self, mock_get):
        """Test notification for task priority change"""
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = {
            'task_id': 52,
            'title': 'High Priority Task',
            'priority': 9,
            'owner': 501,
            'collaborators': [501, 502]
        }
        
        response = self.client.post('/api/events/task-updated',
            json={
                'task_id': 52,
                'changed_fields': ['priority'],
                'actor_id': 501
            }
        )
        
        self.assertEqual(response.status_code, 200)
        
        notifs = Notification.query.filter_by(type='priority_updated').all()
        self.assertGreater(len(notifs), 0)
        self.assertIn('Priority', notifs[0].title)
    
    @patch('notifications.app.requests.get')
    def test_task_status_change_notification(self, mock_get):
        """Test notification for task status change"""
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = {
            'task_id': 53,
            'title': 'Completed Task',
            'status': 'done',
            'owner': 501,
            'collaborators': [501, 502]
        }
        
        response = self.client.post('/api/events/task-updated',
            json={
                'task_id': 53,
                'changed_fields': ['status'],
                'actor_id': 501
            }
        )
        
        self.assertEqual(response.status_code, 200)
        
        notifs = Notification.query.filter_by(type='task_status_updated').all()
        self.assertGreater(len(notifs), 0)
        self.assertIn('Status', notifs[0].title)
    
    @patch('notifications.app.requests.get')
    def test_task_due_date_change_notification(self, mock_get):
        """Test notification for task due date change"""
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = {
            'task_id': 54,
            'title': 'Task with New Deadline',
            'owner': 501,
            'collaborators': [501, 502]
        }
        
        response = self.client.post('/api/events/task-updated',
            json={
                'task_id': 54,
                'changed_fields': ['deadline'],
                'actor_id': 501
            }
        )
        
        self.assertEqual(response.status_code, 200)
        
        notifs = Notification.query.filter_by(type='due_date_changed').all()
        self.assertGreater(len(notifs), 0)
        self.assertIn('Due date', notifs[0].title)
    
    @patch('notifications.app.requests.get')
    def test_collaborators_change_notification(self, mock_get):
        """Test notification when collaborators are updated"""
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = {
            'task_id': 55,
            'title': 'Team Task',
            'owner': 501,
            'collaborators': [501, 502]
        }
        
        response = self.client.post('/api/events/task-updated',
            json={
                'task_id': 55,
                'changed_fields': ['collaborators'],
                'actor_id': 501
            }
        )
        
        self.assertEqual(response.status_code, 200)
        
        notifs = Notification.query.filter_by(type='collaborators_changed').all()
        self.assertGreater(len(notifs), 0)
    
    @patch('notifications.app.requests.get')
    def test_multiple_fields_updated_notification(self, mock_get):
        """Test notification when multiple fields are updated"""
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = {
            'task_id': 56,
            'title': 'Multi-Update Task',
            'status': 'ongoing',
            'priority': 7,
            'owner': 501,
            'collaborators': [501, 502]
        }
        
        response = self.client.post('/api/events/task-updated',
            json={
                'task_id': 56,
                'changed_fields': ['priority', 'status'],
                'actor_id': 501
            }
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Should create notifications for all recipients
        notifs = Notification.query.filter_by(related_task_id=56).all()
        self.assertGreater(len(notifs), 0)
    
    @patch('notifications.app.requests.get')
    def test_all_collaborators_receive_update_notification(self, mock_get):
        """Test that all collaborators receive task update notifications"""
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = {
            'task_id': 57,
            'title': 'Team Collaboration Task',
            'owner': 501,
            'collaborators': [501, 502]
        }
        
        response = self.client.post('/api/events/task-updated',
            json={
                'task_id': 57,
                'changed_fields': ['priority'],
                'actor_id': 501
            }
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Both owner and collaborator should have notifications
        owner_notifs = Notification.query.filter_by(staff_id=501, related_task_id=57).all()
        collab_notifs = Notification.query.filter_by(staff_id=502, related_task_id=57).all()
        
        self.assertGreater(len(owner_notifs), 0)
        self.assertGreater(len(collab_notifs), 0)


class TestNotificationPreferencesIntegration(unittest.TestCase):
    """
    Integration tests for notification preferences affecting all requirements
    """
    
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        self.app = app
        self.client = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()
        
        # Drop and recreate all tables for clean test environment
        db.drop_all()
        db.create_all()
        
        self.staff = Staff(employee_id=601, employee_name="Pref User",
                          email="pref@test.com", password="password123",
                          role="staff", department="IT", team="Dev")
        db.session.add(self.staff)
        db.session.commit()
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()
    
    def test_disable_deadline_reminders(self):
        """Test that users can disable deadline reminders"""
        response = self.client.put('/api/preferences',
            headers={'X-Employee-Id': '601'},
            json={
                'deadline_reminders': False
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertFalse(data['deadline_reminders'])
    
    def test_custom_reminder_days_respected(self):
        """Test that custom reminder days are respected in notifications"""
        # Set only 14 days reminder
        self.client.put('/api/preferences',
            headers={'X-Employee-Id': '601'},
            json={
                'deadline_reminder_days': '14'
            }
        )
        
        prefs = NotificationPreferences.query.get(601)
        reminder_days = prefs.get_reminder_days()
        
        self.assertIn(14, reminder_days)
        self.assertEqual(len(reminder_days), 1)


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)


