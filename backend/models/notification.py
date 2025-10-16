from models.extensions import db
from datetime import datetime

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    notification_id = db.Column(db.String(36), primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.employee_id', ondelete='CASCADE'), nullable=False, index=True)
    type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text)
    related_task_id = db.Column(db.Integer, db.ForeignKey('Task.task_id', ondelete='CASCADE'), nullable=True)
    related_project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=True)
    related_comment_id = db.Column(db.Integer, db.ForeignKey('comments.id', ondelete='CASCADE'), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    read_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.notification_id,
            'staff_id': self.staff_id,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'related_task_id': self.related_task_id,
            'related_project_id': self.related_project_id,
            'related_comment_id': self.related_comment_id,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None
        }

class NotificationPreferences(db.Model):
    __tablename__ = 'notification_preferences'
    
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.employee_id', ondelete='CASCADE'), primary_key=True)
    deadline_reminders = db.Column(db.Boolean, default=True)
    task_status_updates = db.Column(db.Boolean, default=True)
    due_date_changes = db.Column(db.Boolean, default=True)
    # Customizable deadline reminder days (comma-separated, e.g., "7,3,1" or "14,7,3,1")
    deadline_reminder_days = db.Column(db.String(50), default="7,3,1")
    
    def to_dict(self):
        return {
            'staff_id': self.staff_id,
            'deadline_reminders': self.deadline_reminders,
            'task_status_updates': self.task_status_updates,
            'due_date_changes': self.due_date_changes,
            'deadline_reminder_days': self.deadline_reminder_days
        }
    
    def get_reminder_days(self):
        """Parse deadline_reminder_days string into list of integers"""
        try:
            return [int(d.strip()) for d in self.deadline_reminder_days.split(',') if d.strip().isdigit()]
        except Exception:
            return [7, 3, 1]  # Default

class DeadlineNotificationLog(db.Model):
    __tablename__ = 'deadline_notification_log'
    
    log_id = db.Column(db.String(36), primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('Task.task_id', ondelete='CASCADE'), nullable=False, index=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.employee_id', ondelete='CASCADE'), nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('task_id', 'staff_id', 'notification_type', 
                          name='unique_deadline_notification'),
    )