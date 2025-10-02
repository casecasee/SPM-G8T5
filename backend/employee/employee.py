from flask import Flask, request, jsonify, session
from flask_cors import CORS
# from werkzeug.security import generate_password_hash, check_password_hash

from models import db, Staff, Task

app = Flask(__name__)
app.secret_key = "issa_secret_key"
app.config["SESSION_COOKIE_SAMESITE"] = "None"
app.config["SESSION_COOKIE_SECURE"] = True  

CORS(app, supports_credentials=True, origins=["http://localhost:5173"])

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
    
    session['employee_id'] = employee.employee_id
    session['role'] = employee.role

    return {"employee_id": employee.employee_id, "role": employee.role, "employee_name": employee.employee_name} # include name for UI


@app.route('/reset', methods=['POST'])
def reset():
    pass

@app.route('/employees/<department>', methods=['GET'])
def get_employees_by_department(department):
    # used for create task - collaborators are employees in the same department
    employees = Staff.query.filter_by(department=department).all()
    result = []
    for emp in employees:
        emp_data = {
            "employee_id": emp.employee_id,
            "employee_name": emp.employee_name,
            "email": emp.email,
            "department": emp.department,
            "role": emp.role,
            "team": emp.team
        }
        result.append(emp_data)
    return jsonify(result), 200







if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)