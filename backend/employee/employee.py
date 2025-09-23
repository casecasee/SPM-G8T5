from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy 
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
# from invokes import invoke_http

app = Flask(__name__)

CORS(app, origins=["http://localhost:5173"])

# task_url = "http://localhost:5001/task/get_tasks_by_eid"

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

class Manager(Staff):
    __mapper_args__ = {
        "polymorphic_identity": "manager",
    }

    def get_tasks(self):
        # get team members under this manager
        # for each member, get their tasks (call task endpoint)
        # team_members = Staff.query.filter_by(team=self.team).all()
        # tasks = []
        # for member in team_members:
        #     member_tasks = invoke_http(task_url, method='GET', json={"employee_id": member.employee_id})
        #     for item in member_tasks:
        #         if item not in tasks:
        #             tasks.append(item)
        # return tasks

        # # TODO
        pass

class Director(Staff):
    __mapper_args__ = {
        "polymorphic_identity": "director",
    }

    def get_tasks(self):
        # get all employees in this department
        # for each employee, get their tasks (call task endpoint)
        # TODO
        pass

@app.route('/register', methods=['POST'])
def register():

    data = request.json
    name = data.get('employee_name')
    email = data.get('email')
    department = data.get('department')
    role = data.get('role')
    password = data.get('password')
    team = data.get('team')

    employee = Staff.query.filter_by(email=email).first()
    if employee:
        return {"error": "Employee already exists"}, 409

    new_employee = Staff(
        email=email,
        employee_name=name,
        department=department,
        role=role,
        team=team
    )
    new_employee.set_password(password)

    db.session.add(new_employee)
    db.session.commit()
    return {"employee_id": new_employee.employee_id, "role": new_employee.role}, 201

@app.route('/login', methods=['POST'])
def login():
    # input: {email:str, password:str}

    data = request.json
    email = data.get('email')
    password = data.get('password')

    employee = Staff.query.filter_by(email=email).first()

    if not employee:
        return {"error": "Employee does not exist"}, 404
    if not employee.check_password(password):
        return {"error": "Incorrect password"}, 401

    return {"employee_id": employee.employee_id, "role": employee.role} # TODO: RETURN EVERYTHING


@app.route('/reset', methods=['POST'])
def reset():
    pass

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run()