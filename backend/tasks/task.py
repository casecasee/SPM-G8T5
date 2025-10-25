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
from datetime import datetime, timezone, timedelta
import zoneinfo
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
# Only use production database if not testing
if not os.getenv('TESTING'):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URI", "mysql+mysqlconnector://root@localhost:3306/SPM")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

db.init_app(app)

UTC = timezone.utc

def convert_datetime(iso_str: str):
    """
    Accepts ISO 8601 strings like '2025-10-25T18:30:00Z' or with an offset.
    Returns a naive datetime that represents UTC time (for MySQL DATETIME).
    """
    if not isinstance(iso_str, str):
        raise ValueError("deadline must be a string")

    s = iso_str.replace("Z", "+00:00")
    dt = datetime.fromisoformat(s)  # aware if offset present, naive if none

    if dt.tzinfo is None:
        # Decide your policy: reject or assume UTC. Rejecting is safer.
        raise ValueError("deadline must include timezone (e.g., 'Z' or '+00:00')")

    dt_utc = dt.astimezone(timezone.utc).replace(microsecond=0)
    return dt_utc.replace(tzinfo=None)  # naive but represents UTC


# def datetime_now():
#     # replace 'America/New_York' with your actual IANA timezone name
#     local_tz = zoneinfo.ZoneInfo("America/New_York")

#     dt = datetime.now(local_tz)
#     return dt

def get_collaborators(collaborator_ids):
    collaborators = []
    for cid in collaborator_ids:
        staff = Staff.query.get(cid)
        if staff:
            collaborators.append(staff)
    return collaborators

def set_timestamps_by_status(task, old_status, new_status):
    """Set start_date and completed_date based on status transitions"""

    # if initial status is unassigned -> anything, set start_date
    # if new status is done, set completed_date
    # if initial status is None (new task), set start_date if status is anything other than unassigned, set end date as well if done
    # eg if unassigned -> done, set both start and end date

    if old_status == new_status:
        return  # no change

    now = datetime.now()
    if old_status == None: # new task
        if new_status != 'unassigned':
            task.start_date = now
        if new_status == 'done':
            task.completed_date = now
    else:
        if old_status == 'unassigned' and new_status != 'unassigned':
            task.start_date = now
        if new_status == 'done':
            task.completed_date = now

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
            f'{NOTIFICATION_SERVICE_URL}/api/events/task-updated',
            json={
                'task_id': task_id,
                'changed_fields': ['deadline'],
                'actor_id': changed_by_id
            },
            timeout=3
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
    # this endpoint creates handles task and subtask when creating (add task button on frontend)

    # input: {title, description, attachment(o), deadline, project_id(o), collaborators[], priority, owner, }
    data = request.json

    # session info
    eid = session['employee_id']
    role = session['role']
    team = session['team']
    dept = session['department']

    # check if required fields are present
    # title, desc, deadline, priority are compulsory
    # need to check empty strings too
    if 'title' not in data or 'description' not in data or 'deadline' not in data or 'priority' not in data:
        return {"message": "Missing required fields"}, 400

    if not data['title'].strip() or not data['description'].strip():
        return {"message": "Title and description cannot be empty"}, 400

    # allow same title tasks if the task with the same title is completed (to allow recurring tasks with same title)
    existing_tasks = Task.query.filter_by(title=data['title']).all()
    if existing_tasks:
        for task in existing_tasks:
            if task.status in ['ongoing', 'unassigned']:
                return {"message": "Task with this title already exists"}, 400

    # collaborators
    collaborators_ids = data.get('collaborators', [])
    # need to check that the collaborators ids are valid staff ids
    for cid in collaborators_ids:
        staff = Staff.query.get(cid)
        if not staff:
            return {"message": f"Collaborator {cid} not found"}, 404
        
    if data.get('project_id'):
        # if project_id is given, validate that collaborators are part of the project
        project = Project.query.get(data['project_id'])
        if not project:
            return {"message": "Project not found"}, 404
        project_member_ids = [member.employee_id for member in project.members]
        for cid in collaborators_ids:
            if cid not in project_member_ids:
                return {"message": f"Collaborator {cid} is not a member of the project"}, 400
    else:
        # if no project_id, validate that collaborators are in the same dept (lonely tasks)
        dept_staff_ids = [staff.employee_id for staff in Staff.query.filter_by(department=dept).all()]
        for cid in collaborators_ids:
            if cid not in dept_staff_ids:
                return {"message": f"Collaborator {cid} is not in the same department"}, 400
    
    # add owner as collaborator
    if eid not in collaborators_ids:
        collaborators_ids.append(eid)

    collaborators = Staff.query.filter(Staff.employee_id.in_(collaborators_ids)).all()
    
    # handle deadline
    # UTC = timezone.utc
    try:
        deadline = convert_datetime(data['deadline'])
    except ValueError as e:
        return {"message": str(e)}, 400
    if deadline.replace(tzinfo=UTC) <= datetime.now(UTC):
        return {"message": "Deadline must be in the future"}, 400

    # handle attachements
    attachments_json = json.dumps(data.get('attachments', []))

    # handle status
    status = 'ongoing' if role == 'staff' else 'unassigned' 

    # recurrence
    if 'recurrence' in data:
        recurrence = data['recurrence']
        # TODO: validate recurrence (frontend should only be sending numbers) daily - 1, weekly - 7, monthly - 30, custom - any positive int
        if not isinstance(recurrence, int) or recurrence <= 0:
            return {"message": "Recurrence must be a positive integer"}, 400
        

    if 'priority' in data:
        # priority must be an int and between 1-10 
        if not isinstance(data['priority'], int):
            return {"message": "Priority must be an integer"}, 400
        if data['priority'] not in range(1, 11):
            return {"message": "Invalid priority value"}, 400

    # create task object
    new_task = Task(
        title=data['title'],
        description=data['description'],
        attachment=attachments_json,
        deadline=deadline,
        project_id=data.get('project_id'),
        # parent_id=data.get('parent_id'), only for subtasks, handled separately
        priority=data['priority'],
        owner=eid,
        collaborators=collaborators, 
        status=status, 
        recurrence=data.get('recurrence')
    )

    # set timestamps based on status
    set_timestamps_by_status(new_task, None, status)

    # db.session.add(new_task)
    # db.session.commit()

    # id = new_task.task_id

    # subtasks
    try:
        # with db.session.begin():
        db.session.add(new_task)
        db.session.flush()  # to get new_task.task_id
        id = new_task.task_id
        if 'subtasks' in data:
            subtasks_data = data['subtasks']
            for subtask in subtasks_data:
                # check required fields
                if 'title' not in subtask or 'description' not in subtask or 'deadline' not in subtask or 'priority' not in subtask:
                    raise ValueError("Missing required fields in subtask")
                
                if not subtask['title'].strip() or not subtask['description'].strip():
                    raise ValueError("Subtask title and description cannot be empty")

                # handle owner
                sub_owner = subtask.get('owner', eid)  # default to parent task owner if not given
                if sub_owner not in collaborators_ids:
                    raise ValueError(f"Subtask owner {sub_owner} is not a collaborator of the parent task")
                
                # add owner as collaborator
                sub_collaborators_ids = subtask.get('collaborators', [])
                if eid not in sub_collaborators_ids:
                    sub_collaborators_ids.append(eid)
                # make sure subtask collaborators are subset of task collaborators
                for cid in sub_collaborators_ids:
                    if cid not in collaborators_ids:
                        raise ValueError(f"Subtask collaborator {cid} is not a collaborator of the parent task")
                sub_collaborators = Staff.query.filter(Staff.employee_id.in_(sub_collaborators_ids)).all()
                
                # handle deadline
                print(f"Subtask deadline: {subtask['deadline']}, Parent deadline: {deadline}")
                sub_deadline = convert_datetime(subtask['deadline'])
                if sub_deadline.replace(tzinfo=UTC) <= datetime.now(UTC):
                    raise ValueError("Subtask deadline must be in the future")
                # check deadline is before parent task deadline
                if sub_deadline > deadline:
                    raise ValueError("Subtask deadline cannot be after parent task deadline")

                # handle attachments
                sub_attachments_json = json.dumps(subtask.get('attachments', []))

                # handle priority
                if not isinstance(subtask['priority'], int):
                    raise ValueError("Subtask priority must be an integer")
                if subtask['priority'] not in range(1, 11):
                    raise ValueError("Invalid subtask priority value")

                # handle status
                sub_owner_role = Staff.query.get(sub_owner).role.lower()
                sub_status = 'ongoing' if sub_owner_role == 'staff' else 'unassigned'

                # create subtask object
                new_subtask = Task(
                    title=subtask['title'],
                    description=subtask['description'],
                    attachment=sub_attachments_json,
                    deadline=sub_deadline,
                    project_id=data.get('project_id'),
                    parent_id=id,
                    priority=subtask['priority'],
                    owner=sub_owner,
                    collaborators=sub_collaborators,
                    status=sub_status
                )
                # set timestamps based on status
                set_timestamps_by_status(new_subtask, None, sub_status)
                db.session.add(new_subtask)
        db.session.commit()

        return {"message": "Task created", "task_id": id}, 201
    except ValueError as ve:
        db.session.rollback()
        return {"message": str(ve)}, 400

@app.route("/projects/<int:project_id>/timeline", methods=["GET"])
def get_project_timeline(project_id):
    """
    Get timeline data for a specific project
    Returns tasks organized by team members and dates
    """
    try:
        # Get current user info
        current_user_id = session.get('employee_id')
        current_role = session.get('role', '').lower()
        current_department = session.get('department', '')
        
        if not current_user_id:
            return {"error": "Unauthorized"}, 401
        
        # Get project tasks
        project_tasks = Task.query.filter_by(project_id=project_id).all()
        
        if not project_tasks:
            return {
                "project_id": project_id,
                "tasks": [],
                "team_members": []
            }, 200
        
        # Get team members based on role
        team_members = []
        if current_role in ['senior manager', 'hr']:
            # HR/Senior Manager: Get all employees
            team_members = Staff.query.all()
        elif current_role == 'manager':
            # Manager: Get department employees
            team_members = Staff.query.filter_by(department=current_department).all()
        else:
            # Staff: Get department employees (for team context)
            team_members = Staff.query.filter_by(department=current_department).all()
        
        # Convert tasks to timeline format
        timeline_tasks = []
        for task in project_tasks:
            # Filter tasks based on role and permissions
            if current_role == 'staff':
                # Staff can only see their own tasks and team tasks
                if task.owner != current_user_id:
                    # Check if they're a collaborator
                    is_collaborator = any(collab.employee_id == current_user_id for collab in task.collaborators)
                    if not is_collaborator:
                        continue
            
            timeline_tasks.append({
                "id": task.task_id,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "priority": task.priority,
                "due_date": task.deadline.isoformat() if task.deadline else None,
                "owner": task.owner,
                "collaborators": [collab.employee_id for collab in task.collaborators],
                "project_id": task.project_id
            })
        
        # Convert team members to timeline format
        timeline_members = []
        for member in team_members:
            timeline_members.append({
                "employee_id": member.employee_id,
                "employee_name": member.employee_name,
                "role": member.role,
                "department": member.department,
                "team": member.team
            })
        
        # Calculate project date range (first task to last task)
        project_date_range = None
        if timeline_tasks:
            task_dates = [task["due_date"] for task in timeline_tasks if task["due_date"]]
            if task_dates:
                earliest_date = min(task_dates)
                latest_date = max(task_dates)
                project_date_range = {
                    "start_date": earliest_date,
                    "end_date": latest_date
                }
        
        return {
            "project_id": project_id,
            "tasks": timeline_tasks,
            "team_members": timeline_members,
            "project_date_range": project_date_range
        }, 200
        
    except Exception as e:
        print(f"Error in get_project_timeline: {e}")
        return {"error": "Internal server error"}, 500


@app.route("/task/status/<int:task_id>", methods=["PATCH"])
def update_task_status(task_id):
    # This endpoint only updates task status

    # input {status: new_status}
    data = request.json

    # session info
    eid = session['employee_id']
    role = session['role']
    team = session['team']
    dept = session['department']

    # validate input
    if 'status' not in data:
        return {"message": "Missing status field"}, 400
    new_status = data['status']
    if new_status not in ['unassigned', 'ongoing', 'done', 'under review']: # TODO: change 'done' to 'completed' later
        return {"message": "Invalid status value"}, 400
    
    # check if task exists
    curr_task = Task.query.get(task_id)
    if curr_task is None:
        return {"message": "Task not found"}, 404
    
    # only collaborators can update status
    collaborator_ids = [staff.employee_id for staff in curr_task.collaborators]
    if eid not in collaborator_ids:
        return {"message": "Only collaborators can update task status"}, 403
    
    # set timestamps based on status
    old_status = curr_task.status

    if new_status == 'done':
        subtasks = Task.query.filter_by(parent_id=task_id).all()
        for subtask in subtasks:
            if subtask.status != 'done':
                return {"message": "Cannot mark task as done unless all subtasks are done"}, 400
    
    curr_task.status = new_status
    set_timestamps_by_status(curr_task, old_status, new_status)

    # recurrence update
    # TODO: if recurrence is set and status is done, create new task with same details and new deadline based on recurrence (wow)

    if new_status == 'done' and curr_task.recurrence: # this can only happen if all subtasks are done so dont need to check here
        # create new task with same details
        recurrence_days = int(curr_task.recurrence)
        # new deadline is from completion date
        new_deadline = curr_task.completed_date + timedelta(days=recurrence_days)
        new_status = 'unassigned' if role != 'staff' else 'ongoing'
        new_task = Task(
            title=curr_task.title,
            description=curr_task.description,
            attachment=curr_task.attachment,
            deadline=new_deadline,
            project_id=curr_task.project_id,
            priority=curr_task.priority,
            owner=curr_task.owner,
            collaborators=curr_task.collaborators,
            status=new_status,
            recurrence=curr_task.recurrence
        )
        set_timestamps_by_status(new_task, None, new_status)
        # comit here first to get new_task id
        db.session.add(new_task)
        # db.session.flush()  # to get new_task.task_id (maybe not needed)
        # db.session.commit()
        id = new_task.task_id
        #         # need to do subtasks too - subtasks are copied over too
        subtasks = Task.query.filter_by(parent_id=task_id).all()
        for subtask in subtasks:
            # new subtask deadline is offset by same amount as parent task
            new_subtask_deadline = new_deadline - (curr_task.deadline - subtask.deadline)
            # owner should be same as original subtask owner
            new_subtask = Task(
                title=subtask.title,
                description=subtask.description,
                attachment=subtask.attachment,
                deadline=new_subtask_deadline,
                project_id=subtask.project_id,
                parent_id=id,  # link to new parent task
                priority=subtask.priority,
                owner=subtask.owner,
                collaborators=subtask.collaborators,
                status=new_status
            )
            set_timestamps_by_status(new_subtask, None, new_status)
            db.session.add(new_subtask)
        # db.session.add(new_task)

    db.session.commit()

    # SEND NOTIFICATION IF STATUS CHANGED
    if old_status != new_status:
        notify_task_status_updated(task_id, old_status, new_status, eid)
    
    return {"message": "Task status updated"}, 200

@app.route("/task/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    # this endpoint updates task details except status (status will still be given but it will be the same as current status - i think ?)

    # frontend greys out status field, but we still validate it here

    # input: {title, description, attachment(o), deadline, project_id(o), collaborators[], priority, owner, status}
    data = request.json

    # session info
    eid = session['employee_id']
    role = session['role']
    team = session['team']
    dept = session['department']

    # check if task exists
    curr_task = Task.query.get(task_id)
    if curr_task is None:
        return {"message": "Task not found"}, 404
       
    # ---------- NEW: diff-detect main task edits vs. subtask-only edits ----------
    def _current_collab_ids(task):
        try:
            return [s.employee_id for s in task.collaborators]
        except Exception:
            return []

    # Build a minimal diff on top-level fields that belong to the parent task
    main_changes = {}

    # Title
    if 'title' in data and data['title'] != curr_task.title:
        main_changes['title'] = (curr_task.title, data['title'])

    # Description
    if 'description' in data and data['description'] != curr_task.description:
        main_changes['description'] = ('<omitted>', '<omitted>')  # avoid huge diff

    # Deadline (convert before comparing)
    if 'deadline' in data:
        try:
            incoming_deadline = convert_datetime(data['deadline'])
            if curr_task.deadline != incoming_deadline:
                main_changes['deadline'] = (curr_task.deadline, incoming_deadline)
        except ValueError as e:
            return {"message": str(e)}, 400

    # Priority
    if 'priority' in data and data['priority'] != curr_task.priority:
        main_changes['priority'] = (curr_task.priority, data['priority'])

    # Project
    if 'project_id' in data and data['project_id'] != curr_task.project_id:
        main_changes['project_id'] = (curr_task.project_id, data['project_id'])

    # Attachments (normalize to JSON string for stable comparison)
    if 'attachments' in data:
        try:
            incoming_attachments = json.dumps(data['attachments'])
        except Exception:
            return {"message": "Invalid attachments"}, 400
        if (curr_task.attachment or '[]') != (incoming_attachments or '[]'):
            main_changes['attachments'] = ('<omitted>', '<omitted>')

    # Recurrence
    if 'recurrence' in data and data['recurrence'] != curr_task.recurrence:
        main_changes['recurrence'] = (curr_task.recurrence, data['recurrence'])

    # Owner reassignment (this is also a parent-level change)
    if 'owner' in data and data['owner'] != curr_task.owner:
        main_changes['owner'] = (curr_task.owner, data['owner'])

    # Status is not editable here (you already enforce that below), but if frontend sends a different one, treat as a parent change
    if 'status' in data and data['status'] != curr_task.status:
        return {"message": "Status cannot be changed in this endpoint"}, 400

    # If there are parent-level changes and the caller is NOT the parent owner, reject.
    if main_changes and curr_task.owner != eid:
        return {
            "message": "Only the parent task owner can edit parent task fields",
            "blocked_fields": list(main_changes.keys())
        }, 403
    # ---------- END NEW ----------

    
    # Allow task owner OR project manager to update task details
    # If updating project_id, allow project manager to attach task to their project
    if curr_task.owner != eid:
        if 'project_id' in data and data['project_id'] is not None:
            # Check if current user is the project manager
            project = Project.query.get(data['project_id'])
            if not project or project.owner_id != eid:
                return {"message": "Only task owner or project manager can update task details"}, 403
        else:
            return {"message": "Only task owner can update task details"}, 403
    
    # save old deadline for notification
    old_deadline = curr_task.deadline
    old_status = curr_task.status
    
    # validate and update fields
    if 'title' in data:
        curr_task.title = data['title']

    if 'description' in data:
        curr_task.description = data['description']

    if 'deadline' in data:
        deadline = convert_datetime(data['deadline'])
        if deadline.replace(tzinfo=UTC) <= datetime.now(UTC):
            return {"message": "Deadline must be in the future"}, 400
        curr_task.deadline = deadline

    if 'priority' in data:
        curr_task.priority = data['priority']

    # TODO: check if collaborators are subset of project if project_id is given

    if 'attachments' in data:
        curr_task.attachment = json.dumps(data['attachments'])

    if 'status' in data and 'project_id' not in data:
        if curr_task.status != data['status']:
            return {"message": "Status cannot be changed in this endpoint"}, 400
    elif 'status' in data:
        pass
        
    if 'recurrence' in data:
        curr_task.recurrence = data['recurrence']
        # TODO: validate recurrence (frontend should only be sending numbers) daily - 1, weekly - 7, monthly - 30, custom - any positive int
        
    # assign and collaborators thing
        # assign: remove old owner from collaborators, add new owner to collaborators
        # collaborators: ensure owner is in collaborators
        # what if they select a new owner and then
        # either way, just take new collab list and add owner to it (if not already present)

    # assign part
    if 'owner' in data:
        # updating owner; keep quiet in production
        if data['owner'] != curr_task.owner:
            old_owner = curr_task.owner
            curr_task.owner = data['owner']
            # change status to ongoing if staff
            # handle status 
             # status only changes from unassigned to ongoing if owner is staff
             # else remains unchanged
            new_owner_role = Staff.query.get(data['owner']).role.lower()
            if new_owner_role == 'staff':
                if curr_task.status == 'unassigned':
                    curr_task.status = 'ongoing'
    
    set_timestamps_by_status(curr_task, old_status, curr_task.status)

    # 1. check if project_id is given
    #  a. if curr_task.project_id is not None, then we are moving from one project to another (reject)
    #  b. if curr_task.project_id is None, then we are moving from no project to a project (check collaborators)
    # 2. if no project_id is given, then we are dealing with lonely tasks (check collaborators in dept)
    if 'project_id' in data and data['project_id'] is not None:
        if curr_task.project_id is None:
            # moving from no project to a project
            project = Project.query.get(data['project_id'])
            if not project:
                return {"message": "Project not found"}, 404
            project_member_ids = [member.employee_id for member in project.members]
            collaborators_ids = data.get('collaborators', [])
            if collaborators_ids:  # Only validate if collaborators are explicitly provided
                for cid in collaborators_ids:
                    if cid not in project_member_ids:
                        return {"message": f"Collaborator {cid} is not a member of the project"}, 400
            else:
                # If no collaborators provided, preserve existing ones
                collaborators_ids = [collab.employee_id for collab in curr_task.collaborators]
        else:
            # task already has a project; allow if unchanged, reject if changing
            if curr_task.project_id != data['project_id']:
                return {"message": "Cannot change project of an existing task"}, 400
        
    else:
        # lonely task
        collaborators_ids = data.get('collaborators', [])
        dept_staff_ids = [staff.employee_id for staff in Staff.query.filter_by(department=dept).all()]
        for cid in collaborators_ids:
            if cid not in dept_staff_ids:
                return {"message": f"Collaborator {cid} is not in the same department"}, 400
            
    # add owner as collaborator
    if curr_task.owner not in collaborators_ids:
        collaborators_ids.append(curr_task.owner)

    # Update project_id after validation
    if 'project_id' in data:
        curr_task.project_id = data['project_id']

    # Update collaborators in database
    if 'collaborators' in data or 'project_id' in data:
        staff_list = Staff.query.filter(Staff.employee_id.in_(collaborators_ids)).all()
        curr_task.collaborators = staff_list

    db.session.commit()

    # handle subtasks
    # TODO: check this
    # subtasks can be updated or created here
    # if subtask has task_id, update existing subtask
    # else create new subtask
    # omg 

    id = curr_task.task_id

    if 'subtasks' in data:
        subtasks_data = data['subtasks']
        for subtask in subtasks_data:
            if 'task_id' in subtask: # update existing subtask
                subtask_id = subtask['task_id']
                existing_subtask = Task.query.get(subtask_id)
                if existing_subtask is None:
                    return {"message": f"Subtask with id {subtask_id} not found"}, 404
                print("curr_task.owner", curr_task.owner, "existing_subtask.owner", existing_subtask.owner, "eid", eid)
                if existing_subtask.owner != eid and curr_task.owner != eid: # subtask owner and task owner can update subtasks
                    return {"message": f"Only subtask owner or task owner can update subtask with id {subtask_id}"}, 403
                
                # update existing subtask
                # TODO: validate fields - shld make this into a function later
                if 'title' in subtask:
                    # check empty string or spaces
                    if not subtask['title'] or subtask['title'].isspace():
                        return {"message": "Subtask title cannot be empty"}, 400
                    existing_subtask.title = subtask['title']
                if 'description' in subtask:
                    # check empty string or spaces
                    if not subtask['description'] or subtask['description'].isspace():
                        return {"message": "Subtask description cannot be empty"}, 400
                    existing_subtask.description = subtask['description']
                if 'deadline' in subtask:
                    sub_deadline = convert_datetime(subtask['deadline'])
                    if sub_deadline.replace(tzinfo=UTC) <= datetime.now(UTC):
                        return {"message": "Subtask deadline must be in the future"}, 400
                    # check deadline is before parent task deadline
                    if sub_deadline > curr_task.deadline:
                        return {"message": "Subtask deadline cannot be after parent task deadline"}, 400
                    existing_subtask.deadline = sub_deadline
                if 'priority' in subtask:
                    # check priority is int between 1-10
                    if not isinstance(subtask['priority'], int):
                        return {"message": "Subtask priority must be an integer"}, 400
                    if subtask['priority'] not in range(1, 11):
                        return {"message": "Invalid subtask priority value"}, 400
                    existing_subtask.priority = subtask['priority']
                if 'attachments' in subtask:
                    existing_subtask.attachment = json.dumps(subtask.get('attachments', []))

                if 'owner' in subtask:
                    new_owner = subtask['owner']
                    new_owner_role = Staff.query.get(new_owner).role.lower()
                    existing_subtask_owner_role = Staff.query.get(existing_subtask.owner).role.lower()
                    if new_owner != existing_subtask.owner: # assigning subtask (also only downwards)
                        # new subtask owner must be subtset of parent task collaborators
                        if existing_subtask_owner_role == 'staff':
                            return {"message": "Staff cannot assign tasks"}, 400
                        if existing_subtask_owner_role == 'manager' and new_owner_role in ['senior manager', 'hr', 'director', 'manager']:
                            return {"message": "Manager cannot assign tasks upwards"}, 400
                        # TODO: finish business rules for assignment hierarchy
                        if new_owner not in collaborators_ids:
                            return {"message": f"Subtask owner {new_owner} is not a collaborator of the parent task"}, 400
                        existing_subtask.owner = new_owner
                    
                if 'collaborators' in subtask:
                    sub_collaborators_ids = subtask['collaborators']
                    # ensure owner is in collaborators
                    if existing_subtask.owner not in sub_collaborators_ids:
                        sub_collaborators_ids.append(existing_subtask.owner)
                    # make sure subtask collaborators are subset of task collaborators
                    for cid in sub_collaborators_ids:
                        if cid not in collaborators_ids:
                            return {"message": f"Subtask collaborator {cid} is not a collaborator of the parent task"}, 400
                    sub_collaborators = Staff.query.filter(Staff.employee_id.in_(sub_collaborators_ids)).all()
                    existing_subtask.collaborators = sub_collaborators
                
                
            else: # create new subtask

                # TODO: only task owner can create subtasks

                # check required fields
                if 'title' not in subtask or 'description' not in subtask or 'deadline' not in subtask or 'priority' not in subtask:
                    return {"message": "Missing required fields in subtask"}, 400
                
                # check empty strings
                if not subtask['title'].strip() or not subtask['description'].strip():
                    return {"message": "Subtask title and description cannot be empty"}, 400
                
                # priority check
                if not isinstance(subtask['priority'], int):
                    return {"message": "Subtask priority must be an integer"}, 400
                if subtask['priority'] not in range(1, 11):
                    return {"message": "Invalid subtask priority value"}, 400
                
                # add owner as collaborator
                sub_collaborators_ids = subtask.get('collaborators', [])
                if eid not in sub_collaborators_ids:
                    sub_collaborators_ids.append(eid)
                # make sure subtask collaborators are subset of task collaborators
                for cid in sub_collaborators_ids:
                    if cid not in collaborators_ids:
                        return {"message": f"Subtask collaborator {cid} is not a collaborator of the parent task"}, 400
                sub_collaborators = Staff.query.filter(Staff.employee_id.in_(sub_collaborators_ids)).all()
                
                # handle deadline
                sub_deadline = convert_datetime(subtask['deadline'])
                if sub_deadline.replace(tzinfo=UTC) <= datetime.now(UTC):
                    return {"message": "Subtask deadline must be in the future"}, 400
                # check deadline is before parent task deadline
                if sub_deadline > curr_task.deadline:
                    return {"message": "Subtask deadline cannot be after parent task deadline"}, 400
                
                # handle attachments
                sub_attachments_json = json.dumps(subtask.get('attachments', []))

                # handle status
                # TODO: confirm business requirements for subtask status on creation
                sub_status = 'ongoing' if role == 'staff' else 'unassigned' 

                # create subtask object
                new_subtask = Task(
                    title=subtask['title'],
                    description=subtask['description'],
                    attachment=sub_attachments_json,
                    deadline=sub_deadline,
                    project_id=data.get('project_id'), # same as parent task
                    parent_id=id,
                    priority=subtask['priority'],
                    owner=eid,
                    collaborators=sub_collaborators,
                    status=sub_status
                )
                db.session.add(new_subtask)
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
    # Get session data safely
    role = session.get('role', '')
    eid = session.get('employee_id', None)
    team = session.get('team', '')
    dept = session.get('department', '')

    # For now, return all tasks (you can add filtering later based on role)
    # tasks = Task.query.all()
    # tasks_list = [task.to_dict() for task in tasks]
    
    # print(f"DEBUG: Returning {len(tasks_list)} tasks for user {eid} with role {role}")
    # return jsonify({"tasks": tasks_list}), 200

# -----------------------------------------------------------------------------------------------


    # if staff or manager, get all tasks of team.
    # return as {my_tasks: [], team_tasks: [emp1: [list of tasks], emp2: [...]]}
    # if there are subtasks within a task, nest them under parent task

# ----------- New task code: get tasks based on role ---------------------------------------------

    def top_level_tasks_for(employee_id):
        return (Task.query.filter(
                    Task.collaborators.any(employee_id=employee_id),
                    Task.parent_id.is_(None)        # <-- only parents
        ).all())

    # # TODO: move my_tasks_list here to avoid code duplication (minor)

    if (role == 'staff' or role == 'manager') and dept != 'HR': # hr can see all regardless of role
        print('Getting tasks for staff/manager')
        # get all tasks i am a collaborator and owner of
        # my_tasks = Task.query.filter(Task.collaborators.any(employee_id=eid)).all()
        # my_tasks_list = [t.to_dict() for t in my_tasks]
        my_tasks_list = [t.to_dict() for t in top_level_tasks_for(eid)]
        # get all tasks of team members
        team_members = Staff.query.filter_by(team=team).all()
        team_tasks = {}
        for member in team_members:
            if member.employee_id == eid:
                continue
            # member_tasks = Task.query.filter(Task.collaborators.any(employee_id=member.employee_id)).all()
            member_tasks = top_level_tasks_for(member.employee_id)
            team_tasks[member.employee_name] = [t.to_dict() for t in member_tasks]
        
        return jsonify({"my_tasks": my_tasks_list, "team_tasks": team_tasks}), 200


    # if role is director, get all task in the company
    # return as {my_tasks: [], company_tasks: {dept1: {team1: {emp1: [list of tasks], emp2: [...]}, team2: {...}}, dept2: {...}}}
    elif role == 'director' or role == 'senior manager' or dept == 'HR':
        print('Getting tasks for director/senior manager/hr')
        # get all tasks i am a collaborator of (includes those im owner of)
        # my_tasks = Task.query.filter(Task.collaborators.any(employee_id=eid)).all()
        # my_tasks_list = [t.to_dict() for t in my_tasks]
        my_tasks_list = [t.to_dict() for t in top_level_tasks_for(eid)]
        # get all tasks in the company organized by dept, team, employee
        # get all departments
        departments = Staff.query.with_entities(Staff.department).distinct().all() # list of tuples with one element
        company_tasks = {}
        for dept_tuple in departments:
            dept_name = dept_tuple[0]
            dept_members = Staff.query.filter_by(department=dept_name).all()
            dept_dict = {}
            for member in dept_members:
                # member_tasks = Task.query.filter(Task.collaborators.any(employee_id=member.employee_id)).all()
                member_tasks = top_level_tasks_for(member.employee_id)
                team_name = member.team
                if team_name not in dept_dict:
                    dept_dict[team_name] = {}
                dept_dict[team_name][member.employee_name] = [t.to_dict() for t in member_tasks]
            company_tasks[dept_name] = dept_dict

        return jsonify({"my_tasks": my_tasks_list, "company_tasks": company_tasks}), 200


# --------------------------------------------------------------------------------------------------------------
    
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