from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy 
from flask_cors import CORS

from models.extensions import db
from models.task import Task
from models.staff import Staff

app = Flask(__name__)

CORS(app, origins=["http://localhost:5173"])

# task_url = "http://localhost:5001/task/get_tasks_by_eid"

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/SPM'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # suppress warning msgs
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299} # do not timeout

db.init_app(app) # initialise connection to db

def convert_datetime(input_str: str):
    # TODO: convert html input type = date (YYYY-MM-DD) to sql datetime format
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


@app.route('/tasks', methods=['POST'])
def create_task():
    data = request.json

    # input {title, description, attachment(o), deadline, status, project_id, parent_id, employee_id, collaborators[]}
    # send list of collaborators ids, no need include owner id in collaborators

    status = 'ongoing' if data['role'] == 'Staff' else 'unassigned' # set status by role of person creating it
    collaborators = Staff.query.filter(Staff.employee_id.in_(data.get('collaborators', []))).all()

    new_task = Task(
        title=data['title'],
        description=data['description'],
        attachment=data.get('attachment'),
        deadline=convert_datetime(data['deadline']), # datetime is required
        status=status,
        project_id=data.get('project_id'),
        parent_id=data.get('parent_id'),
        owner=data['employee_id'], 
        collaborators=collaborators
    )
    db.session.add(new_task)
    db.session.commit()
    return {"message": "Task created", "task_id": new_task.task_id}, 201

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(port=5002, debug=True)