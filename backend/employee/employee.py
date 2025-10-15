from flask import Flask, request, jsonify, session
from flask_cors import CORS
# from werkzeug.security import generate_password_hash, check_password_hash
import os

from models import db, Staff, Task

app = Flask(__name__)
app.secret_key = "issa_secret_key"
app.config["SESSION_COOKIE_SAMESITE"] = "None"
app.config["SESSION_COOKIE_SECURE"] = True  

CORS(app, supports_credentials=True, origins=["http://localhost:5173", "http://localhost:5174"])

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URI", "mysql+mysqlconnector://root@localhost:3306/SPM")
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
    session['team'] = employee.team
    session['department'] = employee.department

    dept = (employee.department or "").strip()
    team = (employee.team or "").strip()

    return {"employee_id": employee.employee_id, "role": employee.role, "employee_name": employee.employee_name, "department": employee.department, "team": employee.team} 


@app.route('/reset', methods=['POST'])
def reset():
    pass

# @app.route('/tasks', methods=['GET'])
# def get_tasks():
#     eid = request.args.get('eid')
#     role = request.args.get('role')

#     # For now, just return all tasks
#     tasks = Task.query.all()
#     return jsonify([t.to_dict() for t in tasks]), 200

@app.route('/employees/<department>', methods=['GET'])
def get_employees_by_department(department):
    # used for create task - collaborators are employees in the same department
    employees = Staff.query.filter_by(department=department).all()
    result = []
    for emp in employees:
        emp_data = {
            "employee_id": emp.employee_id,
            "employee_name": emp.employee_name,
            # "email": emp.email,
            "department": emp.department,
            "role": emp.role,
            "team": emp.team
        } # frontend asked for id and name, dept, role and team returned jic
        result.append(emp_data)
    return jsonify(result), 200

@app.route('/employees/all', methods=['GET'])
def get_all_employees():
    # used for HR and Senior Manager - can see all employees
    employees = Staff.query.all()
    result = []
    for emp in employees:
        emp_data = {
            "employee_id": emp.employee_id,
            "employee_name": emp.employee_name,
            "department": emp.department,
            "role": emp.role,
            "team": emp.team
        }
        result.append(emp_data)
    return jsonify(result), 200

@app.route('/departments', methods=['GET'])
def get_all_departments():
    # used for HR and Senior Manager - get all unique departments
    departments = db.session.query(Staff.department).distinct().all()
    result = [dept[0] for dept in departments if dept[0]]  # Filter out None values
    return jsonify(result), 200


@app.route('/employee/<int:project_id>', methods=['GET'])
def get_employees_by_project(project_id):
    # used for create task within project - task collaborators are a subset of project collaborators 
    employees = Staff.query.filter(Staff.projects.any(project_id=project_id)).all() 
    result = []
    for emp in employees:
        emp_data = {
            "employee_id": emp.employee_id,
            "employee_name": emp.employee_name,
            "email": emp.email,
            "department": emp.department,
            "role": emp.role,
            "team": emp.team
        } #TODO: return only necessary fields (based on what UI needs)
        result.append(emp_data)
    return jsonify(result), 200

@app.route('/employees/department/<department>/team/<team>', methods=['GET'])
def get_employees_by_department_and_team(department, team):
    """Return all employees in the same department and team (case-insensitive)."""
    department = (department or "").strip()
    team = (team or "").strip()

    employees = Staff.query.filter(
        Staff.department.ilike(department),
        Staff.team.ilike(team)
    ).all()

    result = [
        {
            "employee_id": emp.employee_id,
            "employee_name": emp.employee_name,
            "department": emp.department,
            "role": emp.role,
            "team": emp.team,
        }
        for emp in employees
    ]

    return jsonify(result), 200

# ------------------ Internal API for Other Services ------------------

@app.route('/api/internal/employee/<int:employee_id>', methods=['GET'])
def get_employee_internal(employee_id):
    """
    Internal API for other services to get employee details
    Used by notification service to get employee names
    """
    employee = Staff.query.get(employee_id)
    
    if not employee:
        return jsonify({'error': 'Employee not found'}), 404
    
    return jsonify({
        'employee_id': employee.employee_id,
        'employee_name': employee.employee_name,
        'email': employee.email,
        'department': employee.department,
        'role': employee.role,
        'team': employee.team
    }), 200


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)