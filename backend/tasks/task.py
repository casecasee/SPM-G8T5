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

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__)
app.secret_key = "issa_secret_key" 
app.config["SESSION_COOKIE_SAMESITE"] = "None"
app.config["SESSION_COOKIE_SECURE"] = True  
app.config['UPLOAD_FOLDER'] = 'uploads/attachments'

CORS(app, supports_credentials=True, origins=["http://localhost:5173", "http://localhost:5174"])
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/SPM'
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


@app.route('/tasks', methods=['POST'])
def create_task():
    data = request.json

    # input {title, description, attachment(o), deadline, status, project_id, parent_id, collaborators[], priority, owner}

    role = session['role']
    eid = session['employee_id']

    status = 'ongoing' if role == 'staff' else 'unassigned' # set status by role of person creating it
    
    ppl = data.get('collaborators', [])
    ppl.append(eid) # add owner to collaborators (no need check duplicates because frontend should handle it)
    collaborators = get_collaborators(ppl)

    # TODO: validate deadline (not before today) - frontend job?

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
    print('hereee')

    data = request.json
    new_status = data.get("status")
    eid = session['employee_id']
    curr_task = Task.query.get(task_id)

    print('hereee2')

    if curr_task is None: # check if task exists 
        return {"message": "Task not found"}, 404
    
    print('hereee3')

    # check if employee is a collaborator
    # print(curr_task.collaborators)
    # print(eid)
    print(curr_task.collaborators.filter_by(employee_id=eid).first())
    if curr_task.collaborators.filter_by(employee_id=eid).first() is None:
        print('not collab')
        return {"message": "You are not a collaborator of this task"}, 403
    
    print('hereee4')
    
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

    if curr_task is None: # check if task exists 
        return {"message": "Task not found"}, 404

    if curr_task.owner != eid: # only owner can update task
        return {"message": "Only the owner can update the task"}, 403

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

    if data['owner'] != curr_task.owner and role == 'manager': # owner changed, and only manager can change it
        new_owner = Staff.query.get(data['owner'])
        if new_owner is None:
            return {"message": "New owner not found"}, 404
        curr_task.owner_staff = new_owner
        # TODO: need to update status here
    elif data['owner'] == 'staff':
        return {"message": "Only a manager can assign tasks"}, 403

    if 'collaborators' in data: # update collaborators, dont need to check same depertment etc because frontend should handle it
        ppl = data['collaborators']
        ppl.append(eid) # add owner to collaborators (no need check duplicates because frontend should handle it)
        collaborators = Staff.query.filter(Staff.employee_id.in_(ppl)).all()
        curr_task.collaborators = collaborators

    db.session.commit()
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
    tasks = Task.query.all()
    tasks_list = [task.to_dict() for task in tasks]
    return jsonify({"tasks": tasks_list}), 200
    
@app.route('/attachments/<path:filename>')
def serve_attachment(filename):
    """Serve uploaded files"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    upload_folder = os.path.join(base_dir, '..', 'uploads', 'attachments')
    return send_from_directory(upload_folder, filename)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(port=5002, debug=True)