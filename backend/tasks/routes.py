# backend/tasks/task.py
import os
import time
from flask import Flask, request, jsonify, send_from_directory, make_response
from datetime import datetime
import requests
from flask_cors import CORS
from werkzeug.utils import secure_filename
from models import db, Task
from models.comment import Comment
from models.staff import Staff
import re

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/SPM'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads/attachments'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

CORS(app, supports_credentials=True, origins=["http://localhost:5173", "http://localhost:5174"])
db.init_app(app)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_mentions(content):
    """Parse @mentions from comment content and return mentioned employee IDs"""
    mentioned_ids = set()
    
    # Pattern to match @Name or @123 (numeric IDs)
    mention_pattern = r'@(\w+)'
    matches = re.findall(mention_pattern, content)
    
    for match in matches:
        # Check if it's a numeric ID
        if match.isdigit():
            mentioned_ids.add(int(match))
        else:
            # Try to find employee by name
            try:
                staff = Staff.query.filter(Staff.employee_name.ilike(f'%{match}%')).first()
                if staff:
                    mentioned_ids.add(staff.employee_id)
            except Exception:
                pass
    
    return list(mentioned_ids)

# Separate upload endpoint
@app.route('/upload-attachment', methods=['POST'])
def upload_attachment():
    """Handle file uploads separately"""
    if 'attachment' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['attachment']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"{int(time.time())}_{filename}"
        
        # Create upload directory if it doesn't exist
        upload_dir = app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        
        filepath = os.path.join(upload_dir, unique_filename)
        file.save(filepath)
        
        return jsonify({
            'message': 'File uploaded successfully',
            'file_path': filepath,
            'filename': unique_filename
        }), 200
    
    return jsonify({'error': 'Invalid file type'}), 400

# Serve uploaded files
@app.route('/attachments/<path:filename>')
def serve_attachment(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Your existing task routes (GET, POST, PUT, DELETE) go here...
# Make sure to update the POST /tasks route to accept attachment path

@app.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    # Parse ISO deadline string (e.g. 2025-12-31T12:00:00Z)
    deadline_value = data.get('deadline')
    if isinstance(deadline_value, str):
        try:
            deadline_value = datetime.fromisoformat(deadline_value.replace('Z', '+00:00'))
        except Exception:
            return jsonify({'error': 'Invalid deadline format'}), 400
    
    new_task = Task(
        title=data.get('title'),
        description=data.get('description'),
        attachment=data.get('attachment'),  # File path from upload endpoint
        priority=data.get('priority', 5),
        deadline=deadline_value,
        status=data.get('status', 'ongoing'),
        owner=data.get('employee_id'),
        project_id=data.get('project_id'),  # Optional
        parent_id=data.get('parent_id'),    # Optional, for subtasks
        collaborators=[]
    )
    
    db.session.add(new_task)
    db.session.commit()
    
    # Set collaborators if provided
    collaborator_ids = data.get('collaborators', [])
    if collaborator_ids:
        staff_list = Staff.query.filter(Staff.employee_id.in_(collaborator_ids)).all()
        new_task.collaborators = staff_list
    db.session.commit()
    
    return jsonify(new_task.to_dict()), 201

@app.route('/tasks', methods=['GET'])
def get_tasks():
    """Return all tasks (minimal for scheduler); could be filtered later."""
    tasks = Task.query.all()
    return jsonify([t.to_dict() for t in tasks]), 200

# Legacy compatibility for frontend expecting /task?eid=...&role=...
@app.route('/task', methods=['GET'])
def get_tasks_legacy():
    """Compatibility endpoint matching older frontend requests.

    Accepts optional query params eid and role but currently returns all tasks.
    """
    tasks = Task.query.all()
    return jsonify({'tasks': [t.to_dict() for t in tasks]}), 200

# Legacy compatibility: create task via /task (UI expects this)
@app.route('/task', methods=['POST'])
def create_task_legacy():
    data = request.get_json(force=True) or {}
    deadline_value = data.get('deadline')
    if isinstance(deadline_value, str):
        try:
            deadline_value = datetime.fromisoformat(deadline_value.replace('Z', '+00:00'))
        except Exception:
            return jsonify({'error': 'Invalid deadline format'}), 400

    task = Task(
        title=data.get('title'),
        description=data.get('description'),
        attachment=data.get('attachment'),
        priority=data.get('priority', 5),
        deadline=deadline_value,
        status=data.get('status', 'ongoing'),
        owner=data.get('employee_id'),
        project_id=data.get('project_id'),
        parent_id=data.get('parent_id'),
        collaborators=[]
    )
    db.session.add(task)
    db.session.commit()
    
    # Set collaborators if provided
    collaborator_ids = data.get('collaborators', [])
    if collaborator_ids:
        staff_list = Staff.query.filter(Staff.employee_id.in_(collaborator_ids)).all()
        task.collaborators = staff_list
        db.session.commit()
    
    return jsonify(task.to_dict()), 201

@app.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(task.to_dict()), 200

@app.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.get_json(force=True) or {}
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Not found'}), 404

    changed_fields = []
    old_deadline_str = task.deadline.isoformat() if task.deadline else None

    # Track field changes
    def set_if_changed(attr, key):
        # nonlocal changed_fields
        if key in data and getattr(task, attr) != data.get(key):
            setattr(task, attr, data.get(key))
            changed_fields.append(key)

    set_if_changed('title', 'title')
    set_if_changed('description', 'description')
    set_if_changed('attachment', 'attachment')
    set_if_changed('priority', 'priority')
    # Deadline may be ISO string; convert if present
    if 'deadline' in data:
        new_deadline = data.get('deadline')
        if isinstance(new_deadline, str):
            try:
                parsed = datetime.fromisoformat(new_deadline.replace('Z', '+00:00'))
            except Exception:
                return jsonify({'error': 'Invalid deadline format'}), 400
        else:
            parsed = new_deadline
        if task.deadline != parsed:
            task.deadline = parsed
            changed_fields.append('deadline')
    set_if_changed('status', 'status')

    db.session.commit()

    # Emit notifications events
    NOTIF_BASE = 'http://localhost:5003'
    actor_id = data.get('actor_id')
    try:
        if 'deadline' in changed_fields:
            requests.post(f"{NOTIF_BASE}/api/events/due-date-changed", json={
                'task_id': task_id,
                'old_deadline': old_deadline_str,
                'new_deadline': task.deadline.isoformat() if task.deadline else None,
                'actor_id': actor_id
            }, timeout=3)
        # For other meaningful updates
        meaningful = [f for f in changed_fields if f in ['status', 'title', 'description', 'priority', 'attachment']]
        if meaningful:
            requests.post(f"{NOTIF_BASE}/api/events/task-updated", json={
                'task_id': task_id,
                'changed_fields': meaningful,
                'actor_id': actor_id
            }, timeout=3)
    except Exception:
        # Best-effort; do not fail the update because of notifications
        pass

    return jsonify(task.to_dict()), 200

# Legacy compatibility: update task via /task/<id>
@app.route('/task/<int:task_id>', methods=['PUT', 'OPTIONS'])
def update_task_legacy_route(task_id):
    if request.method == 'OPTIONS':
        # Allow CORS preflight
        return ('', 204)

    data = request.get_json(force=True) or {}
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Not found'}), 404

    changed_fields = []
    old_deadline_str = task.deadline.isoformat() if task.deadline else None

    def set_if_changed(attr, key):
        # nonlocal changed_fields
        if key in data and getattr(task, attr) != data.get(key):
            setattr(task, attr, data.get(key))
            changed_fields.append(key)

    set_if_changed('title', 'title')
    set_if_changed('description', 'description')
    set_if_changed('attachment', 'attachment')
    set_if_changed('priority', 'priority')

    if 'deadline' in data:
        new_deadline = data.get('deadline')
        if isinstance(new_deadline, str):
            try:
                parsed = datetime.fromisoformat(new_deadline.replace('Z', '+00:00'))
            except Exception:
                return jsonify({'error': 'Invalid deadline format'}), 400
        else:
            parsed = new_deadline
        if task.deadline != parsed:
            task.deadline = parsed
            changed_fields.append('deadline')

    set_if_changed('status', 'status')

    # Handle collaborators update
    if 'collaborators' in data:
        collaborator_ids = data.get('collaborators', [])
        if isinstance(collaborator_ids, list):
            staff_list = Staff.query.filter(Staff.employee_id.in_(collaborator_ids)).all()
            task.collaborators = staff_list
            changed_fields.append('collaborators')

    db.session.commit()

    NOTIF_BASE = 'http://localhost:5003'
    actor_id = data.get('actor_id')
    try:
        # Only send due-date-changed notification if deadline was actually changed
        if 'deadline' in changed_fields:
            requests.post(f"{NOTIF_BASE}/api/events/due-date-changed", json={
                'task_id': task_id,
                'old_deadline': old_deadline_str,
                'new_deadline': task.deadline.isoformat() if task.deadline else None,
                'actor_id': actor_id
            }, timeout=3)
        meaningful = [f for f in changed_fields if f in ['status', 'title', 'description', 'priority', 'attachment']]
        if meaningful:
            requests.post(f"{NOTIF_BASE}/api/events/task-updated", json={
                'task_id': task_id,
                'changed_fields': meaningful,
                'actor_id': actor_id
            }, timeout=3)
    except Exception:
        pass

    return jsonify(task.to_dict()), 200

# Comments endpoints expected by UI: /task/<id>/comments
@app.route('/task/<int:task_id>/comments', methods=['GET'])
def list_comments_legacy(task_id):
    comments = Comment.query.filter_by(task_id=task_id).order_by(Comment.created_at.asc()).all()
    return jsonify([c.to_dict() for c in comments]), 200

@app.route('/task/<int:task_id>/comments', methods=['POST'])
def create_comment_legacy(task_id):
    data = request.get_json(force=True) or {}
    content = (data.get('content') or '').strip()
    author_id = data.get('author_id') or data.get('employee_id') or request.headers.get('X-Employee-Id')
    if not content:
        return jsonify({'error': 'Content is required'}), 400
    if not author_id:
        return jsonify({'error': 'author_id or X-Employee-Id header required'}), 400

    comment = Comment(task_id=task_id, author_id=int(author_id), content=content)
    db.session.add(comment)
    db.session.commit()
    
    # Parse mentions from comment
    mentioned_ids = parse_mentions(content)
    
    # Trigger notification for comment creation
    try:
        task = Task.query.get(task_id)
        if task:
            # Get all collaborators + owner for general comment notification
            notify_user_ids = set()
            if task.owner:
                notify_user_ids.add(task.owner)
            try:
                notify_user_ids |= {s.employee_id for s in task.collaborators.all()}
            except Exception:
                pass
            
            # Remove the comment author from general notifications
            notify_user_ids.discard(int(author_id))
            
            print(f"DEBUG: Sending comment notification to users: {notify_user_ids}")
            print(f"DEBUG: Mentioned users: {mentioned_ids}")
            
            # Send general comment notification to collaborators/owner
            for user_id in notify_user_ids:
                response = requests.post(f'http://localhost:5003/api/events/comment-added', 
                    json={
                        'staff_id': user_id,
                        'action': 'added',
                        'title': f'Comments updated: {task.title}',
                        'message': f'New comment added by {author_id}: {content[:100]}{"..." if len(content) > 100 else ""}',
                        'related_task_id': task_id,
                        'related_comment_id': comment.id
                    }, timeout=3)
                print(f"DEBUG: Comment notification response for user {user_id}: {response.status_code}")
            
            # Send mention notifications to mentioned users
            for mentioned_id in mentioned_ids:
                if mentioned_id != int(author_id):  # Don't notify the author
                    response = requests.post(f'http://localhost:5003/api/events/mention', 
                        json={
                            'staff_id': mentioned_id,
                            'title': f'You were mentioned in: {task.title}',
                            'message': f'{author_id} mentioned you in a comment: {content[:100]}{"..." if len(content) > 100 else ""}',
                            'related_task_id': task_id,
                            'related_comment_id': comment.id
                        }, timeout=3)
                    print(f"DEBUG: Mention notification response for user {mentioned_id}: {response.status_code}")
    except Exception as e:
        print(f"DEBUG: Comment notification error: {e}")
        # Best-effort; do not fail comment creation because of notifications
        pass
    
    return jsonify(comment.to_dict()), 201

# Update task status
@app.route('/task/status/<int:task_id>', methods=['PATCH', 'OPTIONS'])
def update_task_status(task_id):
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,X-Employee-Id,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,PATCH,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response, 200
    
    data = request.get_json(force=True) or {}
    new_status = data.get('status')
    employee_id = data.get('employee_id') or request.headers.get('X-Employee-Id')
    
    if not new_status:
        return jsonify({'error': 'Status is required'}), 400
    if not employee_id:
        return jsonify({'error': 'employee_id or X-Employee-Id header required'}), 400
    
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    old_status = task.status
    task.status = new_status
    db.session.commit()
    
    # Trigger notification for status change
    try:
        # Get all collaborators + owner
        notify_user_ids = set()
        if task.owner:
            notify_user_ids.add(task.owner)
        try:
            notify_user_ids |= {s.employee_id for s in task.collaborators.all()}
        except Exception:
            pass
        
        # Remove the actor from notifications
        notify_user_ids.discard(int(employee_id))
        
        print(f"DEBUG: Sending status update notification to users: {notify_user_ids}")
        
        # Send notification to each user
        for user_id in notify_user_ids:
            response = requests.post(f'http://localhost:5003/api/events/task-updated', 
                json={
                    'task_id': task_id,
                    'changed_fields': ['status'],
                    'actor_id': int(employee_id)
                }, timeout=3)
            print(f"DEBUG: Status update notification response for user {user_id}: {response.status_code}")
    except Exception as e:
        print(f"DEBUG: Status update notification error: {e}")
        # Best-effort; do not fail status update because of notifications
        pass
    
    return jsonify({'status': 'ok', 'message': f'Status updated from {old_status} to {new_status}'}), 200

# Update comment
@app.route('/comments/<int:comment_id>', methods=['PUT', 'OPTIONS'])
def update_comment(comment_id):
    if request.method == 'OPTIONS':
        return ('', 204)
    
    data = request.get_json(force=True) or {}
    content = (data.get('content') or '').strip()
    if not content:
        return jsonify({'error': 'Content is required'}), 400
    
    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({'error': 'Comment not found'}), 404
    
    comment.content = content
    comment.updated_at = datetime.utcnow()
    db.session.commit()
    
    # Trigger notification for comment update
    try:
        task = Task.query.get(comment.task_id)
        if task:
            # Get all collaborators + owner
            notify_user_ids = set()
            if task.owner:
                notify_user_ids.add(task.owner)
            try:
                notify_user_ids |= {s.employee_id for s in task.collaborators.all()}
            except Exception:
                pass
            
            # Remove the comment author from notifications
            notify_user_ids.discard(comment.author_id)
            
            print(f"DEBUG: Sending comment update notification to users: {notify_user_ids}")
            
            # Send notification to each user
            for user_id in notify_user_ids:
                response = requests.post(f'http://localhost:5003/api/events/comment-updated', 
                    json={
                        'staff_id': user_id,
                        'action': 'updated',
                        'title': f'Comments updated: {task.title}',
                        'message': f'Comment updated by {comment.author_id}: {content[:100]}{"..." if len(content) > 100 else ""}',
                        'related_task_id': comment.task_id,
                        'related_comment_id': comment.id
                    }, timeout=3)
                print(f"DEBUG: Comment update notification response for user {user_id}: {response.status_code}")
    except Exception as e:
        print(f"DEBUG: Comment update notification error: {e}")
        # Best-effort; do not fail comment update because of notifications
        pass
    
    return jsonify(comment.to_dict()), 200

# Delete comment
@app.route('/comments/<int:comment_id>', methods=['DELETE', 'OPTIONS'])
def delete_comment(comment_id):
    if request.method == 'OPTIONS':
        return ('', 204)
    
    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({'error': 'Comment not found'}), 404
    
    # Store comment info before deletion
    task_id = comment.task_id
    author_id = comment.author_id
    content = comment.content
    
    db.session.delete(comment)
    db.session.commit()
    
    # Trigger notification for comment deletion
    try:
        task = Task.query.get(task_id)
        if task:
            # Get all collaborators + owner
            notify_user_ids = set()
            if task.owner:
                notify_user_ids.add(task.owner)
            try:
                notify_user_ids |= {s.employee_id for s in task.collaborators.all()}
            except Exception:
                pass
            
            # Remove the comment author from notifications
            notify_user_ids.discard(author_id)
            
            print(f"DEBUG: Sending comment delete notification to users: {notify_user_ids}")
            
            # Send notification to each user
            for user_id in notify_user_ids:
                response = requests.post(f'http://localhost:5003/api/events/comment-deleted', 
                    json={
                        'staff_id': user_id,
                        'action': 'deleted',
                        'title': f'Comments updated: {task.title}',
                        'message': f'Comment deleted by {author_id}: {content[:100]}{"..." if len(content) > 100 else ""}',
                        'related_task_id': task_id,
                        'related_comment_id': comment_id
                    }, timeout=3)
                print(f"DEBUG: Comment delete notification response for user {user_id}: {response.status_code}")
    except Exception as e:
        print(f"DEBUG: Comment delete notification error: {e}")
        # Best-effort; do not fail comment deletion because of notifications
        pass
    
    return jsonify({'message': 'Comment deleted'}), 200

# Mentionable users: owner + collaborators (basic)
@app.route('/task/<int:task_id>/mentionable', methods=['GET'])
def list_mentionable_legacy(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify([]), 200
    ids = set()
    if task.owner:
        ids.add(task.owner)
    try:
        ids |= {s.employee_id for s in task.collaborators.all()}
    except Exception:
        pass
    users = Staff.query.filter(Staff.employee_id.in_(list(ids))).all() if ids else []
    return jsonify([
        {
            'employee_id': u.employee_id,
            'employee_name': u.employee_name,
            'role': u.role,
            'department': u.department,
            'team': u.team
        } for u in users
    ]), 200

@app.route('/tasks/<int:task_id>/collaborators', methods=['POST'])
def set_task_collaborators(task_id):
    """Replace collaborators for a task with provided employee_ids.

    Body: { "collaborators": [int, ...], "actor_id": int }
    """
    data = request.get_json(force=True) or {}
    ids = data.get('collaborators') or []
    if not isinstance(ids, list):
        return jsonify({'error': 'collaborators must be a list of employee ids'}), 400

    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Not found'}), 404

    # Fetch Staff objects and set relationship
    staff_list = Staff.query.filter(Staff.employee_id.in_(ids)).all() if ids else []
    task.collaborators = staff_list
    db.session.commit()

    # Notify participants that collaborators changed
    try:
        requests.post(
            'http://localhost:5003/api/events/task-updated',
            json={'task_id': task_id, 'changed_fields': ['collaborators'], 'actor_id': data.get('actor_id')},
            timeout=3
        )
    except Exception:
        pass

    return jsonify(task.to_dict()), 200
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5002)