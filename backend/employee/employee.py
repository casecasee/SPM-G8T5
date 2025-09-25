from flask import Flask, request, jsonify
from flask_cors import CORS
# from werkzeug.security import generate_password_hash, check_password_hash

from models import db, Staff, Task

app = Flask(__name__)

CORS(app, origins=["http://localhost:5173"])

# task_url = "http://localhost:5001/task/get_tasks_by_eid"

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/SPM'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # suppress warning msgs
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299} # do not timeout

db.init_app(app) # initialise connection to db


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

    return {"employee_id": employee.employee_id, "role": employee.role, "employee_name": employee.employee_name} # include name for UI


@app.route('/reset', methods=['POST'])
def reset():
    pass

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run()