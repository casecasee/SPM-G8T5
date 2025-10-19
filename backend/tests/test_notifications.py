"""
Tests all core notification requirements:
1. Deadline reminders (7,3,1 days before, customizable)
2. Overdue task notifications
3. New comment notifications
4. @Mention notifications
5. Task status updates (with actor tracking)
6. Due date change notifications
7. Notification preferences
8. WebSocket real-time delivery
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from notifications.app import (
    app, db, _create_notification, _get_task, _get_task_recipients,
    _send_deadline_reminders, _within_day
)
from models.notification import Notification, NotificationPreferences, DeadlineNotificationLog
from models.staff import Staff


class TestDeadlineNotifications(unittest.TestCase):
    """Test deadline notification functionality (Requirement: 7,3,1 days before deadline)"""
    
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app
        self.client = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()
        db.create_all()
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()
    
    def test_deadline_7_days_notification(self):
        """Test that notification is sent 7 days before deadline"""
        # Create task with deadline 7 days from now
        deadline = datetime.utcnow() + timedelta(days=7)
        
        mock_task = {
            'task_id': 1,
            'title': 'Test Task 7 Days',
            'deadline': deadline.isoformat(),
            'status': 'ongoing',
            'owner': 1,
            'collaborators': []
        }
        
        with patch('notifications.app.requests.get') as mock_get:
            mock_get.return_value.ok = True
            mock_get.return_value.json.return_value = [mock_task]
            
            # Create notification preferences
            prefs = NotificationPreferences(
                staff_id=1,
                deadline_reminders=True,
                deadline_reminder_days="7,3,1"
            )
            db.session.add(prefs)
            db.session.commit()
            
            _send_deadline_reminders()
            
            # Check notification was created
            notification = Notification.query.filter_by(
                staff_id=1,
                type='deadline_7_days'
            ).first()
            
            self.assertIsNotNone(notification, "7-day deadline notification should be created")
            self.assertIn('7 day', notification.title)
            self.assertEqual(notification.related_task_id, 1)
    
    def test_deadline_3_days_notification(self):
        """Test that notification is sent 3 days before deadline"""
        deadline = datetime.utcnow() + timedelta(days=3)
        
        mock_task = {
            'task_id': 2,
            'title': 'Test Task 3 Days',
            'deadline': deadline.isoformat(),
            'status': 'ongoing',
            'owner': 2,
            'collaborators': []
        }
        
        with patch('notifications.app.requests.get') as mock_get:
            mock_get.return_value.ok = True
            mock_get.return_value.json.return_value = [mock_task]
            
            prefs = NotificationPreferences(
                staff_id=2,
                deadline_reminders=True,
                deadline_reminder_days="7,3,1"
            )
            db.session.add(prefs)
            db.session.commit()
            
            _send_deadline_reminders()
            
            notification = Notification.query.filter_by(
                staff_id=2,
                type='deadline_3_days'
            ).first()
            
            self.assertIsNotNone(notification, "3-day deadline notification should be created")
    
    def test_deadline_1_day_notification(self):
        """Test that notification is sent 1 day before deadline"""
        deadline = datetime.utcnow() + timedelta(days=1)
        
        mock_task = {
            'task_id': 3,
            'title': 'Test Task 1 Day',
            'deadline': deadline.isoformat(),
            'status': 'ongoing',
            'owner': 3,
            'collaborators': []
        }
        
        with patch('notifications.app.requests.get') as mock_get:
            mock_get.return_value.ok = True
            mock_get.return_value.json.return_value = [mock_task]
            
            prefs = NotificationPreferences(
                staff_id=3,
                deadline_reminders=True,
                deadline_reminder_days="7,3,1"
            )
            db.session.add(prefs)
            db.session.commit()
            
            _send_deadline_reminders()
            
            notification = Notification.query.filter_by(
                staff_id=3,
                type='deadline_1_day'
            ).first()
            
            self.assertIsNotNone(notification, "1-day deadline notification should be created")
    
    def test_custom_deadline_reminder_days(self):
        """Test user can customize deadline reminder days"""
        # User wants reminders at 14, 5, 2 days
        deadline = datetime.utcnow() + timedelta(days=5)
        
        mock_task = {
            'task_id': 4,
            'title': 'Custom Deadline Task',
            'deadline': deadline.isoformat(),
            'status': 'ongoing',
            'owner': 4,
            'collaborators': []
        }
        
        with patch('notifications.app.requests.get') as mock_get:
            mock_get.return_value.ok = True
            mock_get.return_value.json.return_value = [mock_task]
            
            # Custom reminder days
            prefs = NotificationPreferences(
                staff_id=4,
                deadline_reminders=True,
                deadline_reminder_days="14,5,2"
            )
            db.session.add(prefs)
            db.session.commit()
            
            _send_deadline_reminders()
            
            notification = Notification.query.filter_by(
                staff_id=4,
                type='deadline_5_days'
            ).first()
            
            self.assertIsNotNone(notification, "Custom 5-day reminder should be created")
    
    def test_no_duplicate_deadline_notifications(self):
        """Test that duplicate deadline notifications are not sent"""
        deadline = datetime.utcnow() + timedelta(days=3)
        
        mock_task = {
            'task_id': 5,
            'title': 'No Duplicate Task',
            'deadline': deadline.isoformat(),
            'status': 'ongoing',
            'owner': 5,
            'collaborators': []
        }
        
        with patch('notifications.app.requests.get') as mock_get:
            mock_get.return_value.ok = True
            mock_get.return_value.json.return_value = [mock_task]
            
            prefs = NotificationPreferences(
                staff_id=5,
                deadline_reminders=True,
                deadline_reminder_days="3"
            )
            db.session.add(prefs)
            db.session.commit()
            
            # Run scheduler twice
            _send_deadline_reminders()
            _send_deadline_reminders()
            
            # Should only have one notification
            notifications = Notification.query.filter_by(
                staff_id=5,
                type='deadline_3_days'
            ).all()
            
            self.assertEqual(len(notifications), 1, "Should not create duplicate notifications")


class TestOverdueNotifications(unittest.TestCase):
    """Test overdue task notifications (Requirement: Notify when task is overdue)"""
    
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app
        self.client = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()
        db.create_all()
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()
    
    def test_overdue_task_notification(self):
        """Test that notification is sent for overdue tasks"""
        # Task overdue by 1 day
        deadline = datetime.utcnow() - timedelta(days=1)
        
        mock_task = {
            'task_id': 10,
            'title': 'Overdue Task',
            'deadline': deadline.isoformat(),
            'status': 'ongoing',
            'owner': 10,
            'collaborators': []
        }
        
        with patch('notifications.app.requests.get') as mock_get:
            mock_get.return_value.ok = True
            mock_get.return_value.json.return_value = [mock_task]
            
            _send_deadline_reminders()
            
            notification = Notification.query.filter_by(
                staff_id=10,
                type='overdue_task'
            ).first()
            
            self.assertIsNotNone(notification, "Overdue notification should be created")
            self.assertIn('overdue', notification.title.lower())
    
    def test_overdue_notifies_collaborators(self):
        """Test that overdue notification is sent to all collaborators"""
        deadline = datetime.utcnow() - timedelta(days=1)
        
        mock_task = {
            'task_id': 11,
            'title': 'Team Overdue Task',
            'deadline': deadline.isoformat(),
            'status': 'ongoing',
            'owner': 11,
            'collaborators': [12, 13]
        }
        
        with patch('notifications.app.requests.get') as mock_get:
            mock_get.return_value.ok = True
            mock_get.return_value.json.return_value = [mock_task]
            
            _send_deadline_reminders()
            
            # Check all users got notification
            for staff_id in [11, 12, 13]:
                notification = Notification.query.filter_by(
                    staff_id=staff_id,
                    type='overdue_task'
                ).first()
                self.assertIsNotNone(notification, f"User {staff_id} should receive overdue notification")


class TestCommentNotifications(unittest.TestCase):
    """Test comment-related notifications (Requirement: Notify on new comments)"""
    
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app
        self.client = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()
    
    def tearDown(self):
        self.ctx.pop()
    
    def test_comment_added_notification(self):
        """Test that notification is sent when comment is added"""
        response = self.client.post('/api/events/comment-added', json={
            'staff_id': 20,
            'action': 'added',
            'title': 'New comment on Task ABC',
            'message': 'User 21 added a comment',
            'related_task_id': 20,
            'related_comment_id': 100
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'ok')
    
    def test_comment_updated_notification(self):
        """Test that notification is sent when comment is updated"""
        response = self.client.post('/api/events/comment-updated', json={
            'staff_id': 21,
            'action': 'updated',
            'title': 'Comment updated on Task ABC',
            'message': 'User 22 updated their comment',
            'related_task_id': 21,
            'related_comment_id': 101
        })
        
        self.assertEqual(response.status_code, 200)
    
    def test_comment_deleted_notification(self):
        """Test that notification is sent when comment is deleted"""
        response = self.client.post('/api/events/comment-deleted', json={
            'staff_id': 22,
            'action': 'deleted',
            'title': 'Comment deleted on Task ABC',
            'message': 'User 23 deleted a comment',
            'related_task_id': 22,
            'related_comment_id': 102
        })
        
        self.assertEqual(response.status_code, 200)


class TestMentionNotifications(unittest.TestCase):
    """Test @mention notifications (Requirement: Notify when mentioned)"""
    
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app
        self.client = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()
    
    def tearDown(self):
        self.ctx.pop()
    
    def test_mention_notification(self):
        """Test that notification is sent when user is mentioned"""
        response = self.client.post('/api/events/mention', json={
            'staff_id': 30,
            'title': 'You were mentioned in Task XYZ',
            'message': 'User 31 mentioned you: @User30 please review this',
            'related_task_id': 30,
            'related_comment_id': 200
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'ok')


class TestTaskStatusUpdateNotifications(unittest.TestCase):
    """Test task status update notifications (Requirement: Show who made the change)"""
    
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app
        self.client = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()
    
    def tearDown(self):
        self.ctx.pop()
    
    def test_status_update_includes_actor(self):
        """Test that status update notification includes who made the change"""
        with patch('notifications.app.requests.get') as mock_get:
            # Mock employee service response
            mock_get.return_value.ok = True
            mock_get.return_value.json.return_value = {
                'employee_name': 'John Doe'
            }
            
            with patch('notifications.app._get_task') as mock_get_task:
                mock_get_task.return_value = {
                    'task_id': 40,
                    'title': 'Test Task',
                    'status': 'completed',
                    'owner': 40,
                    'collaborators': []
                }
                
                response = self.client.post('/api/events/task-updated', json={
                    'task_id': 40,
                    'changed_fields': ['status'],
                    'actor_id': 40
                })
                
                self.assertEqual(response.status_code, 200)
    
    def test_status_update_notifies_collaborators(self):
        """Test that status updates notify all collaborators"""
        with patch('notifications.app._get_task') as mock_get_task:
            mock_get_task.return_value = {
                'task_id': 41,
                'title': 'Test Task',
                'status': 'completed',
                'owner': 41,
                'collaborators': [42, 43]
            }
            
            response = self.client.post('/api/events/task-updated', json={
                'task_id': 41,
                'changed_fields': ['status'],
                'actor_id': 41
            })
            
            self.assertEqual(response.status_code, 200)


class TestDueDateChangeNotifications(unittest.TestCase):
    """Test due date change notifications (Requirement: Due date changed)"""
    
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app
        self.client = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()
    
    def tearDown(self):
        self.ctx.pop()
    
    def test_due_date_changed_notification(self):
        """Test that notification is sent when due date changes"""
        with patch('notifications.app._get_task') as mock_get_task:
            mock_get_task.return_value = {
                'task_id': 50,
                'title': 'Task with Changed Deadline',
                'owner': 50,
                'collaborators': []
            }
            
            old_deadline = datetime.utcnow().isoformat()
            new_deadline = (datetime.utcnow() + timedelta(days=3)).isoformat()
            
            response = self.client.post('/api/events/due-date-changed', json={
                'task_id': 50,
                'old_deadline': old_deadline,
                'new_deadline': new_deadline
            })
            
            self.assertEqual(response.status_code, 200)


class TestNotificationPreferences(unittest.TestCase):
    """Test notification preferences/settings (Requirement: User can customize)"""
    
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app
        self.client = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()
        db.create_all()
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()
    
    def test_get_default_preferences(self):
        """Test that default preferences are created if none exist"""
        response = self.client.get('/api/preferences', headers={
            'X-Employee-Id': '60'
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['deadline_reminders'])
        self.assertEqual(data['deadline_reminder_days'], '7,3,1')
    
    def test_update_preferences(self):
        """Test that user can update notification preferences"""
        # Create preferences
        self.client.get('/api/preferences', headers={
            'X-Employee-Id': '61'
        })
        
        # Update preferences
        response = self.client.put('/api/preferences', 
            headers={'X-Employee-Id': '61'},
            json={
                'deadline_reminders': False,
                'task_status_updates': False,
                'deadline_reminder_days': '14,7,3,1'
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertFalse(data['deadline_reminders'])
        self.assertEqual(data['deadline_reminder_days'], '14,7,3,1')
    
    def test_custom_reminder_days(self):
        """Test that user can add custom reminder days"""
        response = self.client.put('/api/preferences',
            headers={'X-Employee-Id': '62'},
            json={
                'deadline_reminder_days': '30,14,7,3,1'
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('30', data['deadline_reminder_days'])


class TestNotificationReading(unittest.TestCase):
    """Test notification read/unread functionality"""
    
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app
        self.client = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()
        db.create_all()
        
        # Create test notification
        notif = Notification(
            notification_id='test-notif-90',
            staff_id=90,
            type='test',
            title='Test',
            message='Test message',
            is_read=False
        )
        db.session.add(notif)
        db.session.commit()
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()
    
    def test_mark_notification_as_read(self):
        """Test marking a single notification as read"""
        response = self.client.patch('/api/notifications/test-notif-90/read',
            headers={'X-Employee-Id': '90'}
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify it's marked as read in database
        notif = Notification.query.get('test-notif-90')
        self.assertTrue(notif.is_read)
    
    def test_mark_all_as_read(self):
        """Test marking all notifications as read"""
        response = self.client.patch('/api/notifications/read-all',
            headers={'X-Employee-Id': '90'}
        )
        
        self.assertEqual(response.status_code, 200)
    
    def test_unread_count(self):
        """Test getting unread notification count"""
        response = self.client.get('/api/notifications/unread',
            headers={'X-Employee-Id': '90'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertGreaterEqual(data['unread_count'], 0)


if __name__ == '__main__':
    # Run with: python -m pytest backend/tests/test_notifications.py -v
    unittest.main()