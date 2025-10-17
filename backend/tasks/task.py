import os
import time
import json
from werkzeug.utils import secure_filename

from flask import Flask, request, jsonify, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy 
from flask_cors import CORS

from models.extensions import db
from models.task import Task
from models.staff import Staff
from models.comment import Comment
from models.comment_mention import CommentMention
from models.comment_attachment import CommentAttachment
from models.project import Project
from datetime import datetime
import re
import os

# ADD these imports at the top (after your existing imports)
import requests

# ADD this constant after your app configuration
NOTIFICATION_SERVICE_URL = "http://localhost:5003"

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__)
app.secret_key = "issa_secret_key" 
app.config["SESSION_COOKIE_SAMESITE"] = "None"
app.config["SESSION_COOKIE_SECURE"] = True  
app.config['UPLOAD_FOLDER'] = 'uploads/attachments'

CORS(app, supports_credentials=True, origins=["http://localhost:5173", "http://localhost:5174"])
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URI", "mysql+mysqlconnector://root@localhost:3306/SPM")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

db.init_app(app)

def convert_datetime(input_str: str):
    from datetime import datetime
    dt = datetime.fromisoformat(input_str)
    return dt

def get_collaborators(collaborator_ids):
    collaborators = []
    for cid in collaborator_ids:
        staff = Staff.query.get(cid)
        if staff:
            collaborators.append(staff)
    return collaborators

def update_stuff_by_status(curr_task, new_status):
    from datetime import datetime
    if curr_task.status == 'unassigned' and new_status == 'ongoing':
        curr_task.start_date = datetime.now()
    elif curr_task.status == 'ongoing' and new_status == 'done':
        curr_task.completed_date = datetime.now()
    # elif curr_task.status == 'ongoing' and new_status == 'under review':
    #     pass
    # elif curr_task.status == 'under review' and new_status == 'done':
    #     curr_task.completed_date = datetime.now()
    curr_task.status = new_status

# ------------------ Notification Helpers ------------------

def get_task_collaborators_ids(task_id):
    """Get list of collaborator employee_ids for a task"""
    task = Task.query.get(task_id)
    if not task:
        return []
    return [c.employee_id for c in task.collaborators.all()]

def get_employee_name(employee_id):
    """Get employee name from Employee service"""
    try:
        response = requests.get(f'http://localhost:5000/api/internal/employee/{employee_id}')
        if response.status_code == 200:
            return response.json().get('employee_name', 'Unknown')
    except Exception as e:
        print(f"Failed to get employee name: {e}")
    return 'Unknown'

def notify_task_status_updated(task_id, old_status, new_status, updated_by_id):
    """Send notification when task status changes"""
    try:
        task = Task.query.get(task_id)
        if not task:
            return
        
        requests.post(
            f'{NOTIFICATION_SERVICE_URL}/api/internal/events/task-status-updated',
            json={
                'task_id': task_id,
                'task_title': task.title,
                'owner_id': task.owner,
                'collaborators': get_task_collaborators_ids(task_id),
                'old_status': old_status,
                'new_status': new_status,
                'updated_by_id': updated_by_id,
                'updated_by_name': get_employee_name(updated_by_id),
                'is_subtask': task.parent_id is not None
            },
            timeout=2
        )
        print(f"[Notification] Sent status update notification for task {task_id}")
    except Exception as e:
        print(f"[Notification] Failed to send status update: {e}")

def notify_task_assigned(task_id, assigned_to, assigned_by_id):
    """Send notification when task is assigned"""
    try:
        task = Task.query.get(task_id)
        if not task:
            return
        
        requests.post(
            f'{NOTIFICATION_SERVICE_URL}/api/internal/events/task-assigned',
            json={
                'task_id': task_id,
                'task_title': task.title,
                'assigned_to': assigned_to,
                'assigned_by_name': get_employee_name(assigned_by_id)
            },
            timeout=2
        )
        print(f"[Notification] Sent assignment notification for task {task_id}")
    except Exception as e:
        print(f"[Notification] Failed to send assignment notification: {e}")

def notify_due_date_changed(task_id, old_date, new_date, changed_by_id):
    """Send notification when due date changes"""
    try:
        task = Task.query.get(task_id)
        if not task:
            return
        
        requests.post(
            f'{NOTIFICATION_SERVICE_URL}/api/internal/events/due-date-changed',
            json={
                'item_id': task_id,
                'item_title': task.title,
                'item_type': 'Subtask' if task.parent_id else 'Task',
                'owner_id': task.owner,
                'collaborators': get_task_collaborators_ids(task_id),
                'old_due_date': old_date.strftime('%Y-%m-%d') if old_date else None,
                'new_due_date': new_date.strftime('%Y-%m-%d') if new_date else None,
                'changed_by_id': changed_by_id,
                'changed_by_name': get_employee_name(changed_by_id)
            },
            timeout=2
        )
        print(f"[Notification] Sent due date change notification for task {task_id}")
    except Exception as e:
        print(f"[Notification] Failed to send due date notification: {e}")

# ------------------ Mentions Helpers ------------------
MENTION_RE = re.compile(r'@(\d+)')  # numeric ids (still supported)
ANY_AT = re.compile(r'@(\S+)')      # any token after '@' up to whitespace

def _normalize_token(value: str) -> str:
    return re.sub(r'[^a-z0-9]', '', (value or '').lower())

def _resolve_name_mentions(allowed_ids: set, name_tokens: set):
    """Resolve @name tokens to employee_ids within allowed_ids.

    - Normalizes both names and tokens by removing non-alnum and lowercasing
    - Returns (resolved_ids, invalid_names, ambiguous_names)
    """
    if not name_tokens:
        return set(), [], []

    # Fetch mentionable users (limited to allowed_ids)
    users = Staff.query.filter(Staff.employee_id.in_(allowed_ids)).all()
    name_key_to_ids = {}
    for u in users:
        key = _normalize_token(u.employee_name)
        if not key:
            continue
        ids = name_key_to_ids.setdefault(key, set())
        ids.add(u.employee_id)

    resolved_ids = set()
    invalid_names = []
    ambiguous_names = []

    for raw in name_tokens:
        key = _normalize_token(raw)
        candidates = list(name_key_to_ids.get(key, []))
        if not candidates:
            invalid_names.append(raw)
        elif len(candidates) > 1:
            ambiguous_names.append(raw)
        else:
            resolved_ids.add(candidates[0])

    return resolved_ids, invalid_names, ambiguous_names

def parse_mentions(content: str):
    tokens = set(ANY_AT.findall(content))
    numeric_tokens = {t for t in tokens if t.isdigit()}
    name_tokens = tokens - numeric_tokens
    numeric_ids = {int(t) for t in numeric_tokens}
    return numeric_ids, name_tokens

def mentionable_ids_for_task(task_id: int):
    t = Task.query.get(task_id)
    if not t:
        return set()
    ids = {t.owner}
    try:
        ids |= {s.employee_id for s in t.collaborators.all()}
    except Exception:
        pass
    if t.project_id:
        p = Project.query.get(t.project_id)
        if p:
            try:
                ids |= {m.employee_id for m in p.members.all()}
            except Exception:
                pass
    return ids

@app.route('/tasks', methods=['POST'])
def create_task():
    data = request.json
    print(data)

    # input {title, description, attachment(o), deadline, project_id, parent_id, collaborators[], priority, owner}

    role = session['role']
    eid = session['employee_id']

    # check if task title already exists
    existing_task = Task.query.filter_by(title=data['title']).first()
    if existing_task:
        return {"message": "Task title already exists"}, 400

    status = 'ongoing' if role == 'staff' else 'unassigned' # set status by role of person creating it
    
    ppl = data.get('collaborators', [])
    ppl.append(eid) # add owner to collaborators (no need check duplicates because frontend should handle it)
    collaborators = get_collaborators(ppl)

    # frontend will make sure deadline is not before today

    # Convert attachments array to JSON string
    attachments_json = json.dumps(data.get('attachments', []))

    new_task = Task(
        title=data['title'],
        description=data['description'],
        attachment=attachments_json,  # Store as JSON string
        deadline=convert_datetime(data['deadline']), # datetime is required
        status=status, # calculated above
        project_id=data.get('project_id'), # o
        parent_id=data.get('parent_id'), # o
        owner=eid, 
        collaborators=collaborators,
        priority=data['priority'] # required 
    )
    db.session.add(new_task)
    db.session.commit()
    return {"message": "Task created", "task_id": new_task.task_id}, 201


@app.route("/task/status/<int:task_id>", methods=["PATCH"])
def update_task_status(task_id):
    
    # input {status, eid}

    data = request.json
    new_status = data.get("status")
    eid = session['employee_id']
    curr_task = Task.query.get(task_id)

    if curr_task is None: # check if task exists 
        return {"message": "Task not found"}, 404

    # check if employee is a collaborator
    if curr_task.collaborators.filter_by(employee_id=eid).first() is None:
        print('not collab')
        return {"message": "You are not a collaborator of this task"}, 403
    
    # SAVE OLD STATUS FOR NOTIFICATION
    old_status = curr_task.status
    
    # update status and other fields accordingly
    # tasks will always pass through ongoing (either by default or after assignment), tasks may or may not pass through under review, tasks will always end at done
    # if status from unassigned -> ongoing, set start_date
    if curr_task.status == 'unassigned' and new_status == 'ongoing':
        curr_task.start_date = time.strftime('%Y-%m-%d %H:%M:%S')

    # unassigned -> under review ?

    # if status from ongoing -> done, set completed_date
    # regardless of start state, if status is done, set completed_date
    elif new_status == 'done':
        curr_task.completed_date = time.strftime('%Y-%m-%d %H:%M:%S')
    
    curr_task.status = new_status
    db.session.commit()

    # SEND NOTIFICATION IF STATUS CHANGED
    if old_status != new_status:
        notify_task_status_updated(task_id, old_status, new_status, eid)
    
    return {"message": "Task status updated"}, 200

@app.route("/task/<int:task_id>", methods=["PUT"])
def update_task(task_id):

    # Update task metadata (not status), frontend sends whole task object
    # This method is not for assigning tasks aka editing owner

    # input {title, description, attachment(o), deadline, status, project_id, parent_id, employee_id, collaborators[], priority, owner}
    data = request.json
    curr_task = Task.query.get(task_id)
    eid = session['employee_id']
    role = session['role']
    # team = session['team'] #TODO: set this in login and use here

    if curr_task is None: # check if task exists 
        return {"message": "Task not found"}, 404

    if curr_task.owner != eid: # only owner can update task
        return {"message": "Only the owner can update the task"}, 403
    
    # SAVE OLD DEADLINE FOR NOTIFICATION
    old_deadline = curr_task.deadline

    # update fields
    curr_task.title = data.get('title', curr_task.title)
    curr_task.description = data.get('description', curr_task.description)
    
    # Handle attachments as JSON array
    if 'attachments' in data:
        curr_task.attachment = json.dumps(data['attachments'])
    
    if 'deadline' in data:
        curr_task.deadline = convert_datetime(data['deadline'])

    curr_task.project_id = data.get('project_id', curr_task.project_id) #TODO: deal with it when doing projects
    curr_task.parent_id = data.get('parent_id', curr_task.parent_id) #TODO: deal with it when doing subtasks
    curr_task.priority = data.get('priority', curr_task.priority)

    if 'status' in data: #TODO: idk if frontend will send status here
        new_status = data['status']
        update_stuff_by_status(curr_task, new_status) 
        # TODO: do the update stuff by status function

    if data['owner'] != curr_task.owner and role == 'manager': # owner changed, and only manager can change it
        new_owner = Staff.query.get(data['owner'])
        if new_owner is None:
            return {"message": "New owner not found"}, 404
        # SEND NOTIFICATION FOR TASK ASSIGNMENT
        old_owner = curr_task.owner
        curr_task.owner_staff = new_owner
        if old_owner != new_owner.employee_id:
            notify_task_assigned(task_id, new_owner.employee_id, eid)
        # TODO: need to update status here
    elif role == 'staff':
        return {"message": "Only a manager can assign tasks"}, 403

    if 'collaborators' in data: # update collaborators, dont need to check same depertment etc because frontend should handle it
        ppl = data['collaborators']
        ppl.append(eid) # add owner to collaborators (no need check duplicates because frontend should handle it)
        collaborators = Staff.query.filter(Staff.employee_id.in_(ppl)).all()
        curr_task.collaborators = collaborators

    db.session.commit()

    # SEND NOTIFICATION IF DEADLINE CHANGED
    if old_deadline != curr_task.deadline:
        notify_due_date_changed(task_id, old_deadline, curr_task.deadline, eid)

    return {"message": "Task updated"}, 200


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
        
        upload_dir = app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        
        filepath = os.path.join(upload_dir, unique_filename)
        file.save(filepath)
        
        return jsonify({
            'message': 'File uploaded successfully',
            'file_path': unique_filename,
            'filename': unique_filename
        }), 200
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route("/tasks", methods=["GET"])
def get_all_tasks():
    role = session['role']
    eid = session['employee_id']
    team = session['team']
    dept = session['department']

    tasks = Task.query.all()
    tasks_list = [task.to_dict() for task in tasks]
    return jsonify({"tasks": tasks_list}), 200

    # TODO: do filter

    # if staff or manager, get all tasks of team.
    # return as {my_tasks: [], team_tasks: [emp1: [list of tasks], emp2: [...]]}

    if role == 'staff' or role == 'manager':
        print('Getting tasks for staff/manager')
        # get all tasks i am a collaborator and owner of
        my_tasks = Task.query.filter(Task.collaborators.any(employee_id=eid)).all()
        my_tasks_list = [t.to_dict() for t in my_tasks]
        # get all tasks of team members
        team_members = Staff.query.filter_by(team=team).all()
        team_tasks = {}
        for member in team_members:
            if member.employee_id == eid:
                continue
            member_tasks = Task.query.filter(Task.collaborators.any(employee_id=member.employee_id)).all()
            team_tasks[member.employee_name] = [t.to_dict() for t in member_tasks]
        
        return jsonify({"my_tasks": my_tasks_list, "team_tasks": team_tasks}), 200


    # if role is director, get all task for department
    # return as {my_tasks: [], dept_tasks : {team_A: [emp1: [list of tasks], emp2: [...]], team_B: [...]}
    elif role == 'director' or role == 'senior manager' or role == 'hr':
        print('Getting tasks for director/senior manager/hr')
        # get all tasks i am a collaborator of (includes those im owner of)
        my_tasks = Task.query.filter(Task.collaborators.any(employee_id=eid)).all()
        my_tasks_list = [t.to_dict() for t in my_tasks]
        # get all tasks of department
        dept_members = Staff.query.filter_by(department=dept).all()
        # loop through members and group responses into team_tasks
        dept_tasks = {} 
        for member in dept_members:
            if member.employee_id == eid:
                continue
            member_tasks = Task.query.filter(Task.collaborators.any(employee_id=member.employee_id)).all()
            team = member.team or "No Team"
            if team not in dept_tasks:
                dept_tasks[team] = {}
            dept_tasks[team][member.employee_name] = [t.to_dict() for t in member_tasks]
        
        return jsonify({"my_tasks": my_tasks_list, "dept_tasks": dept_tasks}), 200


    
@app.route('/attachments/<path:filename>')
def serve_attachment(filename):
    """Serve uploaded files"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    upload_folder = os.path.join(base_dir, '..', 'uploads', 'attachments')
    return send_from_directory(upload_folder, filename)


# ------------------ Comments Endpoints ------------------
@app.route('/task/<int:task_id>/comments', methods=['GET'])
def list_task_comments(task_id):
    comments = Comment.query.filter_by(task_id=task_id).order_by(Comment.created_at.asc()).all()
    def serialize(c):
        atts = CommentAttachment.query.filter_by(comment_id=c.id).all()
        return {**c.to_dict(), "attachments": [
            {"id": a.id, "filename": a.filename, "original_name": a.original_name, "url": f"/attachments/{a.filename}"}
        for a in atts]}
    return jsonify([serialize(c) for c in comments]), 200


@app.route('/task/<int:task_id>/comments', methods=['POST'])
def create_task_comment(task_id):
    if 'employee_id' not in session:
        return {"message": "Unauthorized"}, 401
    data = request.json or {}
    content = (data.get('content') or '').strip()
    if not content:
        return {"message": "Content is required"}, 400

    # validate mentions: allow numeric IDs and @{Name}
    numeric_ids, name_tokens = parse_mentions(content)
    allowed = mentionable_ids_for_task(task_id)
    invalid_ids = numeric_ids - allowed
    resolved_name_ids, invalid_names, ambiguous_names = _resolve_name_mentions(allowed, name_tokens)

    errors = []
    if invalid_ids:
        errors.append(f"Invalid IDs: {sorted(list(invalid_ids))}")
    if invalid_names:
        errors.append(f"Unknown names: {invalid_names}")
    if ambiguous_names:
        errors.append(f"Ambiguous names (not unique): {ambiguous_names}")
    if errors:
        return {"message": "; ".join(errors)}, 400

    attachments = list((data.get('attachments') or []))

    comment = Comment(task_id=task_id, author_id=session['employee_id'], content=content)
    db.session.add(comment)
    db.session.flush()  # get comment.id before commit

    # persist mentions (numeric and resolved names)
    for mid in (numeric_ids | resolved_name_ids):
        db.session.add(CommentMention(comment_id=comment.id, mentioned_id=mid))

    # persist attachments (limit to 10 to avoid abuse)
    for fname in attachments[:10]:
        if isinstance(fname, str) and fname:
            db.session.add(CommentAttachment(comment_id=comment.id, filename=fname))

    db.session.commit()
    # include attachments in response
    resp_atts = [
        {"id": a.id, "filename": a.filename, "url": f"/attachments/{a.filename}"}
        for a in CommentAttachment.query.filter_by(comment_id=comment.id).all()
    ]
    return jsonify({**comment.to_dict(), "attachments": resp_atts}), 201


@app.route('/comments/<int:comment_id>', methods=['PUT'])
def update_comment(comment_id):
    if 'employee_id' not in session:
        return {"message": "Unauthorized"}, 401
    comment = Comment.query.get(comment_id)
    if not comment:
        return {"message": "Not found"}, 404
    if comment.author_id != session['employee_id']:
        return {"message": "Forbidden"}, 403

    data = request.json or {}
    content = (data.get('content') or '').strip()
    if not content:
        return {"message": "Content is required"}, 400

    # validate mentions against the task: allow numeric and names
    numeric_ids, name_tokens = parse_mentions(content)
    allowed = mentionable_ids_for_task(comment.task_id)
    invalid_ids = numeric_ids - allowed
    resolved_name_ids, invalid_names, ambiguous_names = _resolve_name_mentions(allowed, name_tokens)

    errors = []
    if invalid_ids:
        errors.append(f"Invalid IDs: {sorted(list(invalid_ids))}")
    if invalid_names:
        errors.append(f"Unknown names: {invalid_names}")
    if ambiguous_names:
        errors.append(f"Ambiguous names (not unique): {ambiguous_names}")
    if errors:
        return {"message": "; ".join(errors)}, 400

    comment.content = content
    comment.updated_at = datetime.utcnow()

    # rewrite mentions
    CommentMention.query.filter_by(comment_id=comment.id).delete()
    for mid in (numeric_ids | resolved_name_ids):
        db.session.add(CommentMention(comment_id=comment.id, mentioned_id=mid))

    db.session.commit()
    return jsonify(comment.to_dict()), 200


@app.route('/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    if 'employee_id' not in session:
        return {"message": "Unauthorized"}, 401
    comment = Comment.query.get(comment_id)
    if not comment:
        return {"message": "Not found"}, 404

    role = session.get('role')
    if comment.author_id != session['employee_id'] and role != 'manager':
        return {"message": "Forbidden"}, 403

    db.session.delete(comment)
    db.session.commit()
    return '', 204


@app.route('/task/<int:task_id>/mentionable', methods=['GET'])
def list_mentionable(task_id):
    ids = mentionable_ids_for_task(task_id)
    if not ids:
        return jsonify([]), 200
    users = Staff.query.filter(Staff.employee_id.in_(ids)).all()
    return jsonify([
        {
            "employee_id": u.employee_id,
            "employee_name": u.employee_name,
            "role": u.role
        } for u in users
    ]), 200

# ------------------ Internal API for Notification Service ------------------

@app.route('/api/internal/tasks/upcoming-deadlines', methods=['GET'])
def get_upcoming_deadlines():
    """
    Get tasks with deadlines in specified date range
    Used by Notification Service for deadline reminders
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date or not end_date:
        return jsonify({'error': 'start_date and end_date required'}), 400
    
    try:
        # Convert ISO strings to datetime
        from datetime import datetime
        start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    
    # Query tasks with deadlines in range, not completed
    tasks = Task.query.filter(
        Task.deadline >= start,
        Task.deadline <= end,
        Task.status != 'done'  # Your status name for completed
    ).all()
    
    result = []
    for task in tasks:
        result.append({
            'task_id': task.task_id,
            'title': task.title,
            'deadline': task.deadline.strftime('%Y-%m-%d') if task.deadline else None,
            'owner': task.owner,
            'collaborators': get_task_collaborators_ids(task.task_id),
            'is_subtask': task.parent_id is not None
        })
    
    return jsonify({'tasks': result}), 200

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(port=5002, debug=True)


