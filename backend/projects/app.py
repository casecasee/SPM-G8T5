# backend/projects/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173","http://127.0.0.1:5173"])

# TODO: teammate sets this to your MySQL DSN
# Example: 'mysql+mysqlconnector://root:password@localhost:3306/SPM'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/SPM'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    owner = db.Column(db.String(255))
    status = db.Column(db.String(50), nullable=False, default='Active')  # or ENUM
    tasks_done = db.Column(db.Integer, nullable=False, default=0)
    tasks_total = db.Column(db.Integer, nullable=False, default=0)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "owner": self.owner,
            "status": self.status,
            "tasksDone": self.tasks_done,
            "tasksTotal": self.tasks_total,
            "updatedAt": self.updated_at.isoformat(timespec="milliseconds") + "Z",
        }

@app.get('/projects')
def list_projects():
    rows = Project.query.order_by(Project.updated_at.desc()).all()
    return jsonify([p.to_dict() for p in rows])

@app.post('/projects')
def create_project():
    data = request.json or {}
    p = Project(
        name=data.get("name", "Untitled Project"),
        owner=data.get("owner", "Unassigned"),
        status=data.get("status", "Active"),
        tasks_done=data.get("tasksDone", 0),
        tasks_total=data.get("tasksTotal", 0),
        updated_at=datetime.utcnow(),
    )
    db.session.add(p)
    db.session.commit()
    return jsonify(p.to_dict()), 201

@app.patch('/projects/<int:pid>/archive')
def archive(pid: int):
    p = Project.query.get(pid)
    if not p:
        return {"error": "Not found"}, 404
    p.status = "Archived"
    p.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(p.to_dict())

if __name__ == '__main__':
    # For local bootstrap only; in real MySQL use migrations
    with app.app_context():
        db.create_all()
    app.run(port=8001, debug=True)