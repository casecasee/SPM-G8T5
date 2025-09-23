from flask import Flask, request
from sqlalchemy import CheckConstraint
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

CORS(app, origins=["http://localhost:5173"])

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/SPM'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # suppress warning msgs
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299} # do not timeout

db = SQLAlchemy(app) # initialise connection to db

class Staff(db.Model):
    __tablename__ = 'Staff'
    employee_id = db.Column(db.Integer, primary_key=True)
    employee_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False) # 'staff', 'manager', 'director'
    password = db.Column(db.String(255), nullable=False)
    team = db.Column(db.String(100), nullable=False)

    __mapper_args__ = {
        "polymorphic_on": role,
        "polymorphic_identity": "staff",
    }

    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def get_tasks(self):
        # call task endpoint to get tasks by eid
        # tasks = invoke_http(task_url, method='GET', params={"employee_id": self.employee_id})
        # return tasks
    
        # TODO: uncomment after task endpoint is implemented
        pass

Task_Collaborators = db.Table(
    'Task_Collaborators',
    db.Column('task_id', db.Integer, db.ForeignKey('Task.task_id', ondelete='CASCADE'), primary_key=True),
    db.Column('staff_id', db.Integer, db.ForeignKey('Staff.employee_id', ondelete='CASCADE'), primary_key=True),
    mysql_engine="InnoDB"
)

class Task(db.Model):
    __tablename__ = 'Task'

    task_id        = db.Column(db.Integer, primary_key=True)
    title          = db.Column(db.String(255), nullable=False)
    description    = db.Column(db.Text, nullable=False)
    attachment     = db.Column(db.String(512), nullable=True) #TODO: aws s3 link

    # dates / status
    start_date     = db.Column(db.DateTime, nullable=True) # TODO: logic for setting start_date when status changes to IN_PROGRESS
    deadline       = db.Column(db.DateTime, nullable=True, index=True)
    completed_date = db.Column(db.DateTime, nullable=True) # TODO: logic for setting completed_date when status changes to DONE
    status         = db.Column(db.String(32), nullable=False)  # TODO: set status based on role of person who created it

    # owner & project (FKs to other services' tables)
    owner          = db.Column(db.Integer, db.ForeignKey('Staff.employee_id', ondelete='RESTRICT'), nullable=False, index=True)
    # project_id     = db.Column(db.Integer, db.ForeignKey('Project.project_id', ondelete='SET NULL'), nullable=True, index=True)

    # self-referential unary relationship for one-level subtasks
    parent_id      = db.Column(db.Integer, db.ForeignKey('Task.task_id', ondelete='CASCADE'), nullable=True)

    # relationship wiring: parent <-> subtasks
    parent   = db.relationship('Task',
                               remote_side=[task_id],
                               backref=db.backref('subtasks', cascade='all, delete-orphan', lazy='dynamic'),
                               foreign_keys=[parent_id],
                               passive_deletes=True)

    # collaborators many-to-many
    collaborators = db.relationship(
    'Staff',
    secondary=Task_Collaborators,
    lazy='dynamic'
)

    # __table_args__ = (
        # prevent self-loop: a task cannot be its own parent
        # CheckConstraint('parent_id IS NULL OR parent_id <> task_id', name='ck_task_no_self_parent'),)
    
    def __init__(self, title, description, deadline, status, owner, start_date=None, attachment=None, project_id=None, completed_date=None, parent_id=None):
        self.title = title
        self.description = description
        self.deadline = deadline
        self.status = status
        self.owner = owner
        self.start_date = start_date
        self.attachment = attachment 
        self.project_id = project_id
        self.completed_date = completed_date 
        self.parent_id = parent_id

    
    # TODO: one layer of subtasks only
    

def convert_datetime():
    # TODO
    pass


@app.route('/tasks', methods=['POST'])
def create_task():
    data = request.json
    new_task = Task(
        title=data['title'],
        description=data['description'],
        attachment=data.get('attachment'),
        start_date=convert_datetime(data.get('start_date')),
        deadline=convert_datetime(data.get('deadline')),
        completed_date=convert_datetime(data.get('completed_date')),
        status=data['status'],
        owner=data['owner'],
        project_id=data.get('project_id'),
        parent_id=data.get('parent_id')
    )
    db.session.add(new_task)
    db.session.commit()
    return {"message": "Task created", "task_id": new_task.task_id}, 201



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(port=5002)