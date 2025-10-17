from flask import Flask, request, jsonify, session
from flask_cors import CORS, cross_origin
from flask_socketio import SocketIO, emit, join_room
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from models.extensions import db
from models.notification import Notification, NotificationPreferences, DeadlineNotificationLog
from models.staff import Staff
from models.comment import Comment

app = Flask(__name__)
app.secret_key = "issa_secret_key"
app.config["SESSION_COOKIE_SAMESITE"] = "None"
app.config["SESSION_COOKIE_SECURE"] = True

# Update CORS configuration
CORS(app, 
     resources={r"*": {
         "origins": ["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173"],
         "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
         "allow_headers": ["Content-Type", "X-Employee-Id", "Authorization"],
         "supports_credentials": True,
         "expose_headers": ["Content-Type", "Access-Control-Allow-Credentials", "Access-Control-Allow-Origin"]
     }},
     send_wildcard=True)

socketio = SocketIO(app, 
                   cors_allowed_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173"],
                   async_mode='threading',
                   logger=False,
                   engineio_logger=False)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/SPM'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

db.init_app(app)

# Service URLs
EMPLOYEE_SERVICE_URL = "http://localhost:5000"
TASK_SERVICE_URL = "http://localhost:5002"  # Your tasks run on 5002
PROJECT_SERVICE_URL = "http://localhost:8001"  # Assuming projects on 8001

def _room_for_employee(employee_id: str) -> str:
    return f"employee:{employee_id}"

@socketio.on('connect')
def handle_connect():
    employee_id = request.args.get('employee_id')
    if not employee_id:
        return False  # reject connection
    join_room(_room_for_employee(employee_id))
    emit('connected', {'message': f'joined {_room_for_employee(employee_id)}'})

def _create_notification(staff_id: int, notif_type: str, title: str, message: str = None, related_task_id: int = None, related_project_id: int = None, related_comment_id: int = None):
    notification = Notification(
        notification_id=str(uuid.uuid4()),
        staff_id=staff_id,
        type=notif_type,
        title=title,
        message=message,
        related_task_id=related_task_id,
        related_project_id=related_project_id,
        related_comment_id=related_comment_id,
        is_read=False
    )
    db.session.add(notification)
    db.session.commit()



    payload = notification.to_dict()
    socketio.emit('new_notification', payload, room=_room_for_employee(str(staff_id)))
    return payload



def _get_task(task_id: int):
    try:
        resp = requests.get(f"{TASK_SERVICE_URL}/tasks/{task_id}")
        if resp.ok:
            return resp.json()
    except Exception:
        pass
    return None

def _get_task_recipients(task: dict) -> list:
    recipients = []
    owner_id = task.get('owner')
    if owner_id:
        recipients.append(owner_id)
    for sid in task.get('collaborators', []) or []:
        if sid not in recipients:
            recipients.append(sid)
    return recipients

# Global OPTIONS handler for CORS preflight
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,X-Employee-Id,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,PATCH,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response, 200

# Public API: list notifications
@app.route('/api/notifications', methods=['GET'])
def list_notifications():
    staff_id = request.headers.get('X-Employee-Id')
    if not staff_id:
        return jsonify({'error': 'Missing X-Employee-Id'}), 400
    try:
        per_page = int(request.args.get('per_page', 20))
    except ValueError:
        per_page = 20
    notifications = (Notification.query
                     .filter_by(staff_id=int(staff_id))
                     .order_by(Notification.created_at.desc())
                     .limit(per_page)
                     .all())
    return jsonify({'notifications': [n.to_dict() for n in notifications]}), 200

# Public API: unread count
@app.route('/api/notifications/unread', methods=['GET'])
def unread_count():
    staff_id = request.headers.get('X-Employee-Id')
    if not staff_id:
        return jsonify({'error': 'Missing X-Employee-Id'}), 400
    count = Notification.query.filter_by(staff_id=int(staff_id), is_read=False).count()
    return jsonify({'unread_count': count}), 200

# Public API: mark one as read
@app.route('/api/notifications/<notification_id>/read', methods=['PATCH'])
def mark_read(notification_id):
    staff_id = request.headers.get('X-Employee-Id')
    if not staff_id:
        return jsonify({'error': 'Missing X-Employee-Id'}), 400
    n = Notification.query.filter_by(notification_id=notification_id, staff_id=int(staff_id)).first()
    if not n:
        return jsonify({'error': 'Not found'}), 404
    if not n.is_read:
        n.is_read = True
        n.read_at = datetime.now(timezone.utc)
        db.session.commit()
    return jsonify({'status': 'ok'}), 200

# Public API: mark all as read
@app.route('/api/notifications/read-all', methods=['PATCH'])
def mark_all_read():
    staff_id = request.headers.get('X-Employee-Id')
    if not staff_id:
        return jsonify({'error': 'Missing X-Employee-Id'}), 400
    updated = (Notification.query
               .filter_by(staff_id=int(staff_id), is_read=False)
               .update({Notification.is_read: True, Notification.read_at: datetime.now(timezone.utc)}))
    if updated:
        db.session.commit()
    return jsonify({'status': 'ok'}), 200

# Event: mention notification
@app.route('/api/events/mention', methods=['POST'])
def event_mention():
    payload = request.get_json(force=True) or {}
    staff_id = payload.get('staff_id')
    title = payload.get('title')
    message = payload.get('message')
    related_task_id = payload.get('related_task_id')
    related_comment_id = payload.get('related_comment_id')
    
    if not staff_id or not title or not message:
        return jsonify({'error': 'staff_id, title, message required'}), 400
    
    _create_notification(
        staff_id=staff_id, 
        notif_type='mention', 
        title=title, 
        message=message, 
        related_task_id=related_task_id,
        related_comment_id=related_comment_id
    )
    return jsonify({'status': 'ok'}), 200

# Event: comment added/updated/deleted
@app.route('/api/events/comment-added', methods=['POST'])
@app.route('/api/events/comment-updated', methods=['POST'])
@app.route('/api/events/comment-deleted', methods=['POST'])
def event_comment_changed():
    payload = request.get_json(force=True) or {}
    staff_id = payload.get('staff_id')
    action = payload.get('action', 'added')  # added, updated, deleted
    title = payload.get('title')
    message = payload.get('message')
    related_task_id = payload.get('related_task_id')
    related_comment_id = payload.get('related_comment_id')
    
    if not staff_id or not title or not message:
        return jsonify({'error': 'staff_id, title, message required'}), 400
    
    # Use 'comments_updated' for all comment changes
    notif_type = 'comments_updated'
    
    _create_notification(
        staff_id=staff_id, 
        notif_type=notif_type, 
        title=title, 
        message=message, 
        related_task_id=related_task_id,
        related_comment_id=related_comment_id
    )
    return jsonify({'status': 'ok'}), 200

# Event: task updated
@app.route('/api/events/task-updated', methods=['POST'])
def event_task_updated():
    payload = request.get_json(force=True) or {}
    task_id = payload.get('task_id')
    changed_fields = payload.get('changed_fields') or []
    actor_id = payload.get('actor_id')
    if not task_id or not changed_fields:
        return jsonify({'error': 'task_id and changed_fields required'}), 400
    task = _get_task(task_id)
    if not task:
        return jsonify({'error': 'task not found'}), 404
    recipients = _get_task_recipients(task)
    title = f"Task updated: {task.get('title')}"
    message = f"Changed: {', '.join(changed_fields)}"
    
    # Use different notification types based on what changed
    notif_type = 'task_status_updated'  # default
    if 'collaborators' in changed_fields:
        notif_type = 'collaborators_changed'
        title = f"Collaborators updated: {task.get('title')}"
        message = "Task collaborators have been updated"
    elif 'deadline' in changed_fields:
        notif_type = 'due_date_changed'
        title = f"Due date changed: {task.get('title')}"
        message = "Task deadline has been updated"
    elif 'status' in changed_fields:
        notif_type = 'task_status_updated'
        title = f"Status updated: {task.get('title')}"
        # Get actor name
        actor_name = "Someone"
        if actor_id:
            try:
                actor_resp = requests.get(f"{EMPLOYEE_SERVICE_URL}/api/internal/employee/{actor_id}", timeout=2)
                if actor_resp.ok:
                    actor_name = actor_resp.json().get('employee_name', 'Someone')
            except Exception:
                pass
        message = f"{actor_name} changed task status to: {task.get('status', 'unknown')}"
    elif 'priority' in changed_fields:
        notif_type = 'priority_updated'
        title = f"Priority updated: {task.get('title')}"
        message = f"Task priority changed to: {task.get('priority', 'unknown')}"
    elif 'description' in changed_fields:
        notif_type = 'description_updated'
        title = f"Description updated: {task.get('title')}"
        message = "Task description has been updated"
    elif 'title' in changed_fields:
        notif_type = 'name_updated'
        title = f"Task name updated: {task.get('title')}"
        message = "Task name has been updated"
    else:
        # Generic task update for other fields
        notif_type = 'task_status_updated'
        title = f"Task updated: {task.get('title')}"
        message = f"Changed: {', '.join(changed_fields)}"
    
    for staff_id in recipients:
        _create_notification(staff_id=staff_id, notif_type=notif_type, title=title, message=message, related_task_id=task_id)
    return jsonify({'status': 'ok'}), 200

# Event: due date changed
@app.route('/api/events/due-date-changed', methods=['POST'])
def event_due_date_changed():
    payload = request.get_json(force=True) or {}
    task_id = payload.get('task_id')
    old_deadline = payload.get('old_deadline')
    new_deadline = payload.get('new_deadline')
    if not task_id or old_deadline is None or new_deadline is None:
        return jsonify({'error': 'task_id, old_deadline, new_deadline required'}), 400
    task = _get_task(task_id)
    if not task:
        return jsonify({'error': 'task not found'}), 404
    recipients = _get_task_recipients(task)
    title = f"Due date changed: {task.get('title')}"
    message = f"{old_deadline}  {new_deadline}"
    for staff_id in recipients:
        _create_notification(staff_id=staff_id, notif_type='due_date_changed', title=title, message=message, related_task_id=task_id)
    return jsonify({'status': 'ok'}), 200

# Scheduler: approaching deadlines and overdue
scheduler = BackgroundScheduler()

def _within_day(target: datetime, days_from_now: int) -> bool:
    now = datetime.now(timezone.utc)
    start = (now + timedelta(days=days_from_now)).replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return start <= target < end

def _send_deadline_reminders():
    # Fetch tasks via tasks service (unfiltered, then filter here if needed)
    try:
        resp = requests.get(f"{TASK_SERVICE_URL}/tasks")
        if not resp.ok:
            return
        tasks = resp.json()
    except Exception:
        return
    now = datetime.now(timezone.utc)
    for t in tasks:
        deadline_str = t.get('deadline')
        status = t.get('status')
        if not deadline_str or not status or status.lower() in ('done', 'completed'):
            continue
        try:
            deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00')).replace(tzinfo=None)
        except Exception:
            continue
        # Get unique reminder days from all users' preferences
        all_reminder_days = set()
        for staff_id in _get_task_recipients(t):
            prefs = NotificationPreferences.query.get(staff_id)
            if prefs and prefs.deadline_reminders:
                all_reminder_days.update(prefs.get_reminder_days())
            else:
                # Default if no preferences set
                all_reminder_days.update([7, 3, 1])
        
        # Check each reminder day
        for days in sorted(all_reminder_days, reverse=True):
            if _within_day(deadline, days):
                notif_type = f'deadline_{days}_days' if days > 1 else 'deadline_1_day'
                for staff_id in _get_task_recipients(t):
                    # Check user preferences
                    prefs = NotificationPreferences.query.get(staff_id)
                    if prefs and not prefs.deadline_reminders:
                        continue
                    
                    # Check if this user wants this specific reminder day
                    user_days = prefs.get_reminder_days() if prefs else [7, 3, 1]
                    if days not in user_days:
                        continue
                    
                    # de-dup using log
                    exists = DeadlineNotificationLog.query.filter_by(task_id=t.get('task_id'), staff_id=staff_id, notification_type=notif_type).first()
                    if exists:
                        continue
                    title = f"Deadline in {days} day{'s' if days > 1 else ''}: {t.get('title')}"
                    message = f"Due {deadline.strftime('%Y-%m-%d %H:%M')}"
                    _create_notification(staff_id=staff_id, notif_type=notif_type, title=title, message=message, related_task_id=t.get('task_id'))
                    db.session.add(DeadlineNotificationLog(log_id=str(uuid.uuid4()), task_id=t.get('task_id'), staff_id=staff_id, notification_type=notif_type))
                    db.session.commit()

        # Overdue initial
        if deadline < now:
            notif_type = 'overdue_task'
            for staff_id in _get_task_recipients(t):
                exists = DeadlineNotificationLog.query.filter_by(task_id=t.get('task_id'), staff_id=staff_id, notification_type=notif_type).first()
                if exists:
                    continue
                title = f"Task overdue: {t.get('title')}"
                message = f"Was due {deadline.strftime('%Y-%m-%d')}"
                _create_notification(staff_id=staff_id, notif_type=notif_type, title=title, message=message, related_task_id=t.get('task_id'))
                db.session.add(DeadlineNotificationLog(log_id=str(uuid.uuid4()), task_id=t.get('task_id'), staff_id=staff_id, notification_type=notif_type))
                db.session.commit()

scheduler.add_job(_send_deadline_reminders, 'interval', hours=24, id='deadline_reminders')
scheduler.start()

# Add OPTIONS handler for CORS preflight
@app.route('/api/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    """Handle CORS preflight requests"""
    response = jsonify({'status': 'ok'})
    response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', '*'))
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,X-Employee-Id,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,PATCH,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response, 200

# Get notification preferences
@app.route('/api/preferences', methods=['GET'])
def get_preferences():
    staff_id = request.headers.get('X-Employee-Id')
    if not staff_id:
        return jsonify({'error': 'Missing X-Employee-Id'}), 400
    
    prefs = NotificationPreferences.query.get(int(staff_id))
    if not prefs:
        # Create default preferences
        prefs = NotificationPreferences(
            staff_id=int(staff_id),
            deadline_reminders=True,
            task_status_updates=True,
            due_date_changes=True,
            deadline_reminder_days="7,3,1"
        )
        db.session.add(prefs)
        db.session.commit()
    
    return jsonify(prefs.to_dict()), 200

# Update notification preferences
@app.route('/api/preferences', methods=['PUT'])
def update_preferences():
    staff_id = request.headers.get('X-Employee-Id')
    if not staff_id:
        return jsonify({'error': 'Missing X-Employee-Id'}), 400
    
    data = request.get_json(force=True) or {}
    prefs = NotificationPreferences.query.get(int(staff_id))
    
    if not prefs:
        prefs = NotificationPreferences(staff_id=int(staff_id))
        db.session.add(prefs)
    
    if 'deadline_reminders' in data:
        prefs.deadline_reminders = data['deadline_reminders']
    if 'task_status_updates' in data:
        prefs.task_status_updates = data['task_status_updates']
    if 'due_date_changes' in data:
        prefs.due_date_changes = data['due_date_changes']
    if 'deadline_reminder_days' in data:
        prefs.deadline_reminder_days = data['deadline_reminder_days']
    
    db.session.commit()
    return jsonify(prefs.to_dict()), 200

# Clear old notifications for testing
@app.route('/api/clear-notifications', methods=['POST'])
def clear_notifications():
    """Clear all notifications for testing purposes"""
    try:
        Notification.query.delete()
        db.session.commit()
        return jsonify({'message': 'All notifications cleared'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    socketio.run(app, debug=True, port=5003)