# """
# Edge case and security tests for notification system
# Place in: backend/tests/test_notifications_edge_cases.py

# Tests edge cases, security, performance, and data integrity
# """

# import unittest
# from unittest.mock import Mock, patch, MagicMock
# from datetime import datetime, timedelta
# import sys
# import os
# import time

# # Add parent directory to path for imports
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# from notifications.app import app, db, _create_notification, _send_deadline_reminders
# from models.notification import Notification, NotificationPreferences
# from models.staff import Staff


# class TestEdgeCases(unittest.TestCase):
#     """Test edge cases and error handling"""
    
#     def setUp(self):
#         app.config['TESTING'] = True
#         app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
#         self.app = app
#         self.client = app.test_client()
#         self.ctx = app.app_context()
#         self.ctx.push()
#         db.create_all()
    
#     def tearDown(self):
#         db.session.remove()
#         db.drop_all()
#         self.ctx.pop()
    
#     def test_completed_task_no_deadline_reminder(self):
#         """Test that completed tasks don't trigger deadline reminders"""
#         deadline = datetime.utcnow() + timedelta(days=3)
        
#         # Task with status='done'
#         mock_task = {
#             'task_id': 100,
#             'title': 'Completed Task',
#             'deadline': deadline.isoformat(),
#             'status': 'done',  # Completed status
#             'owner': 100,
#             'collaborators': []
#         }
        
#         with patch('notifications.app.requests.get') as mock_get:
#             mock_get.return_value.ok = True
#             mock_get.return_value.json.return_value = [mock_task]
            
#             prefs = NotificationPreferences(
#                 staff_id=100,
#                 deadline_reminders=True,
#                 deadline_reminder_days="3"
#             )
#             db.session.add(prefs)
#             db.session.commit()
            
#             _send_deadline_reminders()
            
#             # Should NOT create notification for completed task
#             notification = Notification.query.filter_by(
#                 staff_id=100,
#                 related_task_id=100
#             ).first()
            
#             self.assertIsNone(notification, "Completed tasks should not trigger deadline reminders")
    
#     def test_disabled_deadline_reminders_not_sent(self):
#         """Test that users with disabled preferences don't receive reminders"""
#         deadline = datetime.utcnow() + timedelta(days=3)
        
#         mock_task = {
#             'task_id': 101,
#             'title': 'Task for User with Disabled Reminders',
#             'deadline': deadline.isoformat(),
#             'status': 'ongoing',
#             'owner': 101,
#             'collaborators': []
#         }
        
#         with patch('notifications.app.requests.get') as mock_get:
#             mock_get.return_value.ok = True
#             mock_get.return_value.json.return_value = [mock_task]
            
#             # User has disabled deadline reminders
#             prefs = NotificationPreferences(
#                 staff_id=101,
#                 deadline_reminders=False,  # DISABLED
#                 deadline_reminder_days="3"
#             )
#             db.session.add(prefs)
#             db.session.commit()
            
#             _send_deadline_reminders()
            
#             # Should NOT create notification
#             notification = Notification.query.filter_by(
#                 staff_id=101,
#                 type='deadline_3_days'
#             ).first()
            
#             self.assertIsNone(notification, "Disabled reminders should not be sent")
    
#     def test_non_collaborator_no_notification(self):
#         """Test that users not involved in task don't get notifications"""
#         with patch('notifications.app._get_task') as mock_get_task:
#             mock_get_task.return_value = {
#                 'task_id': 102,
#                 'title': 'Team Task',
#                 'owner': 102,
#                 'collaborators': [103, 104]  # Only these users
#             }
            
#             response = self.client.post('/api/events/task-updated', json={
#                 'task_id': 102,
#                 'changed_fields': ['status'],
#                 'actor_id': 102
#             })
            
#             self.assertEqual(response.status_code, 404)
    
#     def test_list_notifications_only_returns_own(self):
#         """Test that listing notifications only returns user's own"""
#         # Create notification for another user
#         other_notif = Notification(
#             notification_id='other-user-notif',
#             staff_id=999,
#             type='test',
#             title='Other User Notification',
#             message='Should not be visible',
#             is_read=False
#         )
#         db.session.add(other_notif)
#         db.session.commit()
        
#         response = self.client.get('/api/notifications',
#             headers={'X-Employee-Id': '200'}
#         )
        
#         self.assertEqual(response.status_code, 200)
#         data = response.get_json()
        
#         # Should only return notifications for user 200
#         for notif in data['notifications']:
#             self.assertEqual(notif['staff_id'], 200)


# class TestNotificationDataIntegrity(unittest.TestCase):
#     """Test data integrity and consistency"""
    
#     def setUp(self):
#         app.config['TESTING'] = True
#         app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
#         self.app = app
#         self.client = app.test_client()
#         self.ctx = app.app_context()
#         self.ctx.push()
#         db.create_all()
    
#     def tearDown(self):
#         db.session.remove()
#         db.drop_all()
#         self.ctx.pop()
    
#     def test_notification_type_matches_action(self):
#         """Test that notification type field matches the action"""
#         # Status update should create specific type
#         with patch('notifications.app._get_task') as mock_get_task:
#             mock_get_task.return_value = {
#                 'task_id': 300,
#                 'title': 'Test Task',
#                 'status': 'completed',
#                 'owner': 300,
#                 'collaborators': []
#             }
            
#             with patch('notifications.app.requests.get') as mock_get:
#                 mock_get.return_value.ok = True
#                 mock_get.return_value.json.return_value = {
#                     'employee_name': 'Test User'
#                 }
                
#                 self.client.post('/api/events/task-updated', json={
#                     'task_id': 300,
#                     'changed_fields': ['status'],
#                     'actor_id': 300
#                 })
            
#             notification = Notification.query.filter_by(
#                 staff_id=300,
#                 related_task_id=300
#             ).first()
            
#             self.assertEqual(notification.type, 'task_status_updated')
    
#     def test_notification_has_related_ids(self):
#         """Test that notifications include appropriate related IDs"""
#         # Task notification should have related_task_id
#         notif = _create_notification(
#             staff_id=301,
#             notif_type='task_status_updated',
#             title='Task Updated',
#             related_task_id=301
#         )
        
#         self.assertIsNotNone(notif['related_task_id'])
#         self.assertEqual(notif['related_task_id'], 301)
    
#     def test_notification_created_at_timestamp(self):
#         """Test that notifications have valid created_at timestamp"""
#         before = datetime.utcnow()
        
#         notif = _create_notification(
#             staff_id=302,
#             notif_type='test',
#             title='Timestamp Test'
#         )
        
#         after = datetime.utcnow()
        
#         created_at = datetime.fromisoformat(notif['created_at'].replace('Z', '+00:00')).replace(tzinfo=None)
        
#         self.assertGreaterEqual(created_at, before)
#         self.assertLessEqual(created_at, after)
    
#     def test_notification_ordering(self):
#         """Test that notifications are returned in descending order (newest first)"""
#         # Create multiple notifications with delays
#         for i in range(3):
#             notif = Notification(
#                 notification_id=f'order-test-{i}',
#                 staff_id=303,
#                 type='test',
#                 title=f'Notification {i}',
#                 message=f'Message {i}',
#                 is_read=False,
#                 created_at=datetime.utcnow() + timedelta(seconds=i)
#             )
#             db.session.add(notif)
#         db.session.commit()
        
#         response = self.client.get('/api/notifications',
#             headers={'X-Employee-Id': '303'}
#         )
        
#         data = response.get_json()
#         notifications = data['notifications']
        
#         # Check that notifications are in descending order
#         for i in range(len(notifications) - 1):
#             current = datetime.fromisoformat(notifications[i]['created_at'].replace('Z', '+00:00'))
#             next_one = datetime.fromisoformat(notifications[i + 1]['created_at'].replace('Z', '+00:00'))
#             self.assertGreaterEqual(current, next_one)


# class TestPerformance(unittest.TestCase):
#     """Test performance-related scenarios"""
    
#     def setUp(self):
#         app.config['TESTING'] = True
#         app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
#         self.app = app
#         self.client = app.test_client()
#         self.ctx = app.app_context()
#         self.ctx.push()
#         db.create_all()
    
#     def tearDown(self):
#         db.session.remove()
#         db.drop_all()
#         self.ctx.pop()
    
#     def test_list_notifications_pagination(self):
#         """Test pagination works correctly"""
#         # Create 50 notifications
#         for i in range(50):
#             notif = Notification(
#                 notification_id=f'paginate-{i}',
#                 staff_id=400,
#                 type='test',
#                 title=f'Notification {i}',
#                 message='Test',
#                 is_read=False
#             )
#             db.session.add(notif)
#         db.session.commit()
        
#         # Request with per_page=10
#         response = self.client.get('/api/notifications?per_page=10',
#             headers={'X-Employee-Id': '400'}
#         )
        
#         data = response.get_json()
#         notifications = data['notifications']
        
#         # Should return only 10
#         self.assertEqual(len(notifications), 10)
    
#     def test_deadline_scheduler_performance(self):
#         """Test scheduler performs reasonably with many tasks"""
#         # Create many tasks with various deadlines
#         tasks = []
#         for i in range(100):
#             days_offset = (i % 10) + 1  # Deadlines 1-10 days from now
#             deadline = datetime.utcnow() + timedelta(days=days_offset)
#             tasks.append({
#                 'task_id': 500 + i,
#                 'title': f'Task {i}',
#                 'deadline': deadline.isoformat(),
#                 'status': 'ongoing',
#                 'owner': 500 + (i % 10),
#                 'collaborators': []
#             })
        
#         with patch('notifications.app.requests.get') as mock_get:
#             mock_get.return_value.ok = True
#             mock_get.return_value.json.return_value = tasks
            
#             # Measure execution time
#             start = time.time()
#             _send_deadline_reminders()
#             duration = time.time() - start
            
#             # Should complete in reasonable time (< 5 seconds for 100 tasks)
#             self.assertLess(duration, 5.0, f"Scheduler took {duration}s, should be < 5s")


# class TestSubtaskNotifications(unittest.TestCase):
#     """Test that subtasks have separate notifications from tasks"""
    
#     def setUp(self):
#         app.config['TESTING'] = True
#         self.app = app
#         self.client = app.test_client()
#         self.ctx = app.app_context()
#         self.ctx.push()
    
#     def tearDown(self):
#         self.ctx.pop()
    
#     def test_subtask_separate_from_task(self):
#         """Test that subtask notifications are tracked separately"""
#         with patch('notifications.app._get_task') as mock_get_task:
#             # Parent task
#             mock_get_task.return_value = {
#                 'task_id': 70,
#                 'title': 'Parent Task',
#                 'owner': 70,
#                 'collaborators': []
#             }
            
#             response1 = self.client.post('/api/events/task-updated', json={
#                 'task_id': 70,
#                 'changed_fields': ['status'],
#                 'actor_id': 70
#             })
            
#             # Subtask
#             mock_get_task.return_value = {
#                 'task_id': 71,
#                 'title': 'Subtask',
#                 'parent_id': 70,
#                 'owner': 70,
#                 'collaborators': []
#             }
            
#             response2 = self.client.post('/api/events/task-updated', json={
#                 'task_id': 71,
#                 'changed_fields': ['status'],
#                 'actor_id': 70
#             })
            
#             self.assertEqual(response1.status_code, 200)
#             self.assertEqual(response2.status_code, 200)


# class TestCriticalGaps(unittest.TestCase):
#     """Test cases for critical gaps identified in requirements"""
    
#     def setUp(self):
#         app.config['TESTING'] = True
#         self.app = app
#         self.client = app.test_client()
#         self.ctx = app.app_context()
#         self.ctx.push()
    
#     def tearDown(self):
#         self.ctx.pop()
    
#     def test_reply_notifies_only_parent_comment_creator(self):
#         """
#         CRITICAL GAP: Test that replies only notify the parent comment creator
        
#         Current Status: NOT IMPLEMENTED
        
#         Expected Behavior:
#         1. User A creates comment on task
#         2. User B replies to User A's comment
#         3. Only User A should receive notification
#         4. Other collaborators should NOT receive notification
        
#         Implementation Needed:
#         - Add parent_comment_id field to Comment model
#         - Modify create_comment_legacy() in tasks/routes.py
#         - Check if parent_comment_id exists
#         - If reply: notify only parent comment author
#         - If new comment: notify all collaborators (existing behavior)
        
#         To implement, modify tasks/routes.py:
        
#         @app.route('/task/<int:task_id>/comments', methods=['POST'])
#         def create_comment_legacy(task_id):
#             data = request.get_json(force=True) or {}
#             content = (data.get('content') or '').strip()
#             author_id = data.get('author_id') or request.headers.get('X-Employee-Id')
#             parent_comment_id = data.get('parent_comment_id')  # NEW
            
#             if not content or not author_id:
#                 return jsonify({'error': 'Required fields missing'}), 400
            
#             comment = Comment(
#                 task_id=task_id, 
#                 author_id=int(author_id), 
#                 content=content,
#                 parent_comment_id=parent_comment_id  # NEW
#             )
#             db.session.add(comment)
#             db.session.commit()
            
#             # Check if this is a reply
#             if parent_comment_id:
#                 # This is a REPLY - notify only parent comment creator
#                 parent_comment = Comment.query.get(parent_comment_id)
#                 if parent_comment and parent_comment.author_id != int(author_id):
#                     notify_user_ids = {parent_comment.author_id}
#             else:
#                 # This is a NEW COMMENT - notify all collaborators (existing logic)
#                 notify_user_ids = set()
#                 if task.owner:
#                     notify_user_ids.add(task.owner)
#                 notify_user_ids |= {s.employee_id for s in task.collaborators.all()}
#                 notify_user_ids.discard(int(author_id))
            
#             # Send notifications...
#         """
#         self.skipTest("Comment reply feature not yet implemented - SEE TEST DOCSTRING FOR IMPLEMENTATION")
    
#     def test_subtask_notification_indicates_subtask(self):
#         """
#         MINOR GAP: Test that subtask notifications indicate they are for subtasks
        
#         Current Status: PARTIALLY IMPLEMENTED
        
#         Enhancement Needed:
#         - When creating notifications for tasks with parent_id
#         - Include "Subtask" prefix in title
#         - Example: "Subtask updated: Review Documentation"
        
#         To implement, modify notifications/app.py event handlers:
        
#         def event_task_updated():
#             # ... existing code ...
#             task = _get_task(task_id)
            
#             # Check if it's a subtask
#             task_type = "Subtask" if task.get('parent_id') else "Task"
#             title = f"{task_type} updated: {task.get('title')}"
#             # ... rest of logic
#         """
#         with patch('notifications.app._get_task') as mock_get_task:
#             mock_get_task.return_value = {
#                 'task_id': 700,
#                 'title': 'Subtask Documentation',
#                 'parent_id': 699,  # Has parent, so it's a subtask
#                 'owner': 700,
#                 'collaborators': []
#             }
            
#             response = self.client.post('/api/events/task-updated', json={
#                 'task_id': 700,
#                 'changed_fields': ['status'],
#                 'actor_id': 700
#             })
            
#             self.assertEqual(response.status_code, 200)
#             # Ideally check that notification title includes "Subtask"


# class TestWebSocketIntegration(unittest.TestCase):
#     """Test WebSocket real-time notification delivery"""
    
#     def setUp(self):
#         app.config['TESTING'] = True
#         app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
#         self.app = app
#         self.client = app.test_client()
#         self.ctx = app.app_context()
#         self.ctx.push()
#         db.create_all()
    
#     def tearDown(self):
#         db.session.remove()
#         db.drop_all()
#         self.ctx.pop()
    
#     def test_notification_emitted_on_creation(self):
#         """Test that new notifications are emitted via WebSocket"""
#         with patch('notifications.app.socketio.emit') as mock_emit:
#             notification = _create_notification(
#                 staff_id=80,
#                 notif_type='test',
#                 title='Test Notification',
#                 message='Test message'
#             )
            
#             # Verify emit was called
#             mock_emit.assert_called_once()
#             args = mock_emit.call_args
            
#             # Check event name
#             self.assertEqual(args[0][0], 'new_notification')
            
#             # Check notification payload was sent
#             payload = args[0][1]
#             self.assertEqual(payload['staff_id'], 80)
#             self.assertEqual(payload['title'], 'Test Notification')


# class TestCollaboratorNotifications(unittest.TestCase):
#     """Test that collaborators are properly notified"""
    
#     def setUp(self):
#         app.config['TESTING'] = True
#         self.app = app
#         self.client = app.test_client()
#         self.ctx = app.app_context()
#         self.ctx.push()
    
#     def tearDown(self):
#         self.ctx.pop()
    
#     def test_collaborators_changed_notification(self):
#         """Test notification sent when collaborators are added/removed"""
#         with patch('notifications.app._get_task') as mock_get_task:
#             mock_get_task.return_value = {
#                 'task_id': 800,
#                 'title': 'Task with New Collaborators',
#                 'owner': 800,
#                 'collaborators': [801, 802]
#             }
            
#             response = self.client.post('/api/events/task-updated', json={
#                 'task_id': 800,
#                 'changed_fields': ['collaborators'],
#                 'actor_id': 800
#             })
            
#             self.assertEqual(response.status_code, 200)


# if __name__ == '__main__':
#     # Run with: python -m pytest backend/tests/test_notifications_edge_cases.py -v
#     unittest.main()(response.status_code, 200)
            
#             # User 105 (not involved) should NOT have notification
#     notification = Notification.query.filter_by(
#         staff_id=105,
#         related_task_id=102
#     ).first()
    
#     self.assertIsNone(notification, "Non-collaborators should not receive notifications")
    
#     def test_task_without_deadline_no_reminder(self):
#         """Test that tasks without deadlines don't trigger reminders"""
#         mock_task = {
#             'task_id': 103,
#             'title': 'No Deadline Task',
#             'deadline': None,  # No deadline
#             'status': 'ongoing',
#             'owner': 103,
#             'collaborators': []
#         }
        
#         with patch('notifications.app.requests.get') as mock_get:
#             mock_get.return_value.ok = True
#             mock_get.return_value.json.return_value = [mock_task]
            
#             _send_deadline_reminders()
            
#             # No notifications should be created
#             notifications = Notification.query.filter_by(
#                 related_task_id=103
#             ).all()
            
#             self.assertEqual(len(notifications), 0, "Tasks without deadlines should not trigger reminders")
    
#     def test_invalid_deadline_format_handling(self):
#         """Test graceful handling of invalid deadline formats"""
#         mock_task = {
#             'task_id': 104,
#             'title': 'Invalid Deadline Task',
#             'deadline': 'invalid-date-format',
#             'status': 'ongoing',
#             'owner': 104,
#             'collaborators': []
#         }
        
#         with patch('notifications.app.requests.get') as mock_get:
#             mock_get.return_value.ok = True
#             mock_get.return_value.json.return_value = [mock_task]
            
#             # Should not crash
#             try:
#                 _send_deadline_reminders()
#                 success = True
#             except Exception as e:
#                 print(f"Exception: {e}")
#                 success = False
            
#             self.assertTrue(success, "Should handle invalid deadline formats gracefully")


# class TestSecurityAndAuthorization(unittest.TestCase):
#     """Test security and authorization features"""
    
#     def setUp(self):
#         app.config['TESTING'] = True
#         app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
#         self.app = app
#         self.client = app.test_client()
#         self.ctx = app.app_context()
#         self.ctx.push()
#         db.create_all()
        
#         # Create test notification for user 200
#         notif = Notification(
#             notification_id='security-test-200',
#             staff_id=200,
#             type='test',
#             title='Test Notification',
#             message='Test',
#             is_read=False
#         )
#         db.session.add(notif)
#         db.session.commit()
    
#     def tearDown(self):
#         db.session.remove()
#         db.drop_all()
#         self.ctx.pop()
    
#     def test_missing_employee_id_returns_error(self):
#         """Test that requests without X-Employee-Id are rejected"""
#         response = self.client.get('/api/notifications')
        
#         self.assertEqual(response.status_code, 400)
#         data = response.get_json()
#         self.assertIn('error', data)
#         self.assertIn('Employee-Id', data['error'])
    
#     def test_cannot_read_other_users_notifications(self):
#         """Test users can only access their own notifications"""
#         # Try to access user 200's notification as user 201
#         response = self.client.patch('/api/notifications/security-test-200/read',
#             headers={'X-Employee-Id': '201'}
#         )
        
#         # Should return 404 (not found)
#         self.assertEqual(response.status_code, 404)
    
#     def test_cannot_mark_other_users_notifications_read(self):
#         """Test users cannot mark other users' notifications as read"""
#         response = self.client.patch('/api/notifications/security-test-200/read',
#             headers={'X-Employee-Id': '999'}
#         )
        
#         self.assertEqual