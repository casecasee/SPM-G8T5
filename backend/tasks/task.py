from flask import Flask, request, jsonify
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


@app.route('/tasks', methods=['POST'])
def create_task():
    data = request.json

    # input {title, description, attachment(o), deadline, status, project_id, parent_id, employee_id, collaborators[]}

    status = 'ongoing' if data['role'] == 'Staff' else 'unassigned' # set status by role of person creating it
    ppl = data.get('collaborators', [])
    ppl.append(data['employee_id']) # add owner to collaborators (no need check duplicates because frontend should handle it)
    collaborators = Staff.query.filter(Staff.employee_id.in_(ppl)).all()

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


@app.route("/task/status/<int:task_id>", methods=["PATCH"])
def update_task_status(task_id):
    
    # input {status, eid}

    data = request.json
    new_status = data.get("status")
    eid = data.get("eid")
    curr_task = Task.query.get(task_id)

    if curr_task is None: # check if task exists 
        return {"message": "Task not found"}, 404

    # check if employee is a collaborator
    if curr_task.collaborators.filter_by(employee_id=eid).first() is None:
        return {"message": "You are not a collaborator of this task"}, 403
    
    # update status and other fields accordingly
    # if status from unassigned -> ongoing, set start_date



    # unassigned -> under review ?


    # if status from ongoing -> done, set completed_date


@app.route("/tasks", methods=["GET"])
def get_all_tasks():
    tasks = Task.query.all()
    tasks_list = [task.to_dict() for task in tasks]
    return jsonify({"tasks": tasks_list}), 200
    


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(port=5002, debug=True)