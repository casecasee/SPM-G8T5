# backend/projects/app.py
from flask import Flask, request, jsonify
import json
from urllib.request import urlopen
from urllib.error import URLError
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from models import db, Project, Staff
from sqlalchemy import func

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173","http://127.0.0.1:5173"])

# TODO: teammate sets this to your MySQL DSN
# Example: 'mysql+mysqlconnector://root:password@localhost:3306/SPM'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/SPM'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


@app.get('/projects')
def list_projects():
    rows = Project.query.order_by(Project.updated_at.desc()).all()

    # Try to fetch all tasks once from tasks service and aggregate per project
    project_id_to_counts = {}
    try:
        with urlopen('http://localhost:5002/tasks', timeout=2) as resp:
            body = resp.read().decode('utf-8')
            payload = json.loads(body)
            tasks = payload.get('tasks') or []
            for t in tasks:
                pid = t.get('project_id')
                if not pid:
                    continue
                stats = project_id_to_counts.setdefault(pid, {'total': 0, 'done': 0})
                stats['total'] += 1
                if (t.get('status') or '').lower() == 'done':
                    stats['done'] += 1
    except URLError:
        # tasks service not available; fall back to stored counters
        project_id_to_counts = {}
    except Exception:
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