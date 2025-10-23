# backend/projects/app.py
from flask import Flask, request, jsonify, session
import json
from urllib.request import urlopen
from urllib.error import URLError
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from models import db, Project, Staff
from models.project import project_members
from models.task import Task
from sqlalchemy import func
import os

app = Flask(__name__)
app.secret_key = "issa_secret_key"
app.config["SESSION_COOKIE_SAMESITE"] = "None"
app.config["SESSION_COOKIE_SECURE"] = True

CORS(app, supports_credentials=True, origins=["http://localhost:5173","http://127.0.0.1:5173"])

# TODO: teammate sets this to your MySQL DSN
# Example: 'mysql+mysqlconnector://root:password@localhost:3306/SPM'
# Only use production database if not testing
if not os.getenv('TESTING'):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URI", "mysql+mysqlconnector://root@localhost:3306/SPM")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


@app.get('/projects')
def list_projects():
    # Get current user info (same pattern as other endpoints)
    current_user_id = session.get('employee_id')
    current_role = session.get('role', '').lower()
    current_department = session.get('department', '')
    
    # Authentication check
    if not current_user_id:
        return {"error": "Unauthorized"}, 401
    
    # Role-based project filtering
    if current_role in ['senior manager', 'hr', 'director']:
        # Senior managers, HR, and directors can see all projects
        rows = Project.query.order_by(Project.updated_at.desc()).all()
    elif current_role == 'manager':
        # Managers can see projects in their department
        # Join with project_members and staff tables to filter by department
        rows = Project.query.join(project_members).join(Staff).filter(
            Staff.department == current_department
        ).order_by(Project.updated_at.desc()).all()
    else:
        # Staff can only see projects they are members of
        rows = Project.query.join(project_members).filter(
            project_members.c.staff_id == current_user_id
        ).order_by(Project.updated_at.desc()).all()

    # Query tasks directly from database to count per project
    project_id_to_counts = {}
    try:
        tasks = Task.query.all()
        print(f"DEBUG: Fetched {len(tasks)} tasks from database")
        for task in tasks:
            pid = task.project_id
            if not pid:
                continue
            print(f"DEBUG: Task {task.task_id} has project_id {pid}")
            stats = project_id_to_counts.setdefault(pid, {'total': 0, 'done': 0})
            stats['total'] += 1
            if task.status and task.status.lower() == 'done':
                stats['done'] += 1
        print(f"DEBUG: Project counts: {project_id_to_counts}")
    except Exception as e:
        print(f"DEBUG: Error querying tasks: {e}")
        project_id_to_counts = {}

    # Build response, overriding counters when we have live stats
    result = []
    for p in rows:
        d = p.to_dict()
        counts = project_id_to_counts.get(d['id'])
        if counts:
            d['tasksTotal'] = counts['total']
            d['tasksDone'] = counts['done']
        result.append(d)
    return jsonify(result)

@app.post('/projects')
def create_project():
    data = request.json or {}

    def parse_iso(z):
        if not z:
            return None
        try:
            return datetime.fromisoformat(z.replace('Z', '+00:00'))
        except Exception:
            return None

    p = Project(
        name=data.get("name", "Untitled Project"),
        owner=data.get("owner", "Unassigned"),
        owner_id=data.get("ownerId"),
        status=data.get("status", "Active"),
        # Counters are computed from tasks service; start at 0
        tasks_done=0,
        tasks_total=0,
        updated_at=datetime.utcnow(),
    )
    # New: optional project-level due date
    p.due_date = parse_iso(data.get("dueDate"))
    db.session.add(p)
    members = data.get("members") or []
    if members:
        p.members = Staff.query.filter(Staff.employee_id.in_(members)).all()
    db.session.commit()
    return jsonify(p.to_dict()), 201

# Archive endpoint removed per product decision

if __name__ == '__main__':
    # For local bootstrap only; in real MySQL use migrations
    with app.app_context():
        db.create_all()
    app.run(port=8001, debug=True)