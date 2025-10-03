from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy 
from flask_cors import CORS

from models.extensions import db
from models.task import Task
from models.staff import Staff

app = Flask(__name__)
app.secret_key = "issa_secret_key" 
app.config["SESSION_COOKIE_SAMESITE"] = "None"
app.config["SESSION_COOKIE_SECURE"] = True  


CORS(app, supports_credentials=True, origins=["http://localhost:5173", "http://localhost:5174"])
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

    # input {title, description, attachment(o), deadline, status, project_id, parent_id, employee_id, collaborators[], priority}

    status = 'ongoing' if data['role'] == 'staff' else 'unassigned' # set status by role of person creating it
    ppl = data.get('collaborators', [])
    ppl.append(data['employee_id']) # add owner to collaborators (no need check duplicates because frontend should handle it)
    collaborators = Staff.query.filter(Staff.employee_id.in_(ppl)).all()

    # TODO: validate deadline (not before today) - frontend job?

    new_task = Task(
        title=data['title'],
        description=data['description'],
        attachment=data.get('attachment'),
        deadline=convert_datetime(data['deadline']), # datetime is required
        status=status,
        project_id=data.get('project_id'),
        parent_id=data.get('parent_id'),
        owner=data['employee_id'], 
        collaborators=collaborators,
        priority=data.get('priority') 
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


@app.route("/task/<int:task_id>", methods=["PUT"])
def update_task(task_id):

    # Update task metadata (not status), frontend sends whole task object
    # This method is not for assigning tasks aka editing owner

    # input {title, description, attachment(o), deadline, status, project_id, parent_id, employee_id, collaborators[], priority}
    data = request.json
    curr_task = Task.query.get(task_id)

    if curr_task is None: # check if task exists 
        return {"message": "Task not found"}, 404

    eid = data.get("employee_id")
    if curr_task.owner != eid: # only owner can update task
        return {"message": "Only the owner can update the task"}, 403

    # update fields
    curr_task.title = data.get('title', curr_task.title)
    curr_task.description = data.get('description', curr_task.description)
    curr_task.attachment = data.get('attachment', curr_task.attachment)
    if 'deadline' in data:
        curr_task.deadline = convert_datetime(data['deadline'])
    curr_task.project_id = data.get('project_id', curr_task.project_id) #TODO: deal with it when doing projects
    curr_task.parent_id = data.get('parent_id', curr_task.parent_id) #TODO: deal with it when doing subtasks
    curr_task.priority = data.get('priority', curr_task.priority)

    if 'status' in data: #TODO: idk if frontend will send status here
        new_status = data['status']
        update_stuff_by_status(curr_task, new_status)

    if 'collaborators' in data: # update collaborators, dont need to check same depertment etc because frontend should handle it
        ppl = data['collaborators']
        ppl.append(eid) # add owner to collaborators (no need check duplicates because frontend should handle it)
        collaborators = Staff.query.filter(Staff.employee_id.in_(ppl)).all()
        curr_task.collaborators = collaborators

    db.session.commit()
    return {"message": "Task updated"}, 200

@app.route("/tasks", methods=["GET"])
def get_all_tasks():
    tasks = Task.query.all()
    tasks_list = [task.to_dict() for task in tasks]
    print(session)
    print(session.keys())


    return jsonify({"tasks": tasks_list}), 200
    


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(port=5002, debug=True)