from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy 
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

CORS(app, origins=["http://localhost:5173"])

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/SPM'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # suppress warning msgs
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299} # do not timeout

db = SQLAlchemy(app) # initialise connection to db

class Employee(db.Model):
    __tablename__ = 'Employee'
    employee_id = db.Column(db.Integer, primary_key=True)
    employee_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    department = db.Column(db.String(100))
    role = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(255), nullable=False)

@app.route('/login', methods=['POST'])
def login():
    # input: {email:str, password:str}

    data = request.json
    email = data.get('email')
    password = data.get('password')


    employee = Employee.query.filter_by(email=email).first()

    if not employee:
        return {"error": "Employee does not exist"}, 404
    if not check_password_hash(employee.password, password):
        return {"error": "Incorrect password"}, 401
    
    EID = employee.employee_id
    role = employee.role

    return {"employee_id": EID, "role": role}

@app.route('/register', methods=['POST'])
def register():
    # input: {email:str, employee_name:str, department:str, role:str, password:str}

    data = request.json
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')
    department = data.get('department')
    employee_name = data.get('employee_name')

    employee = Employee.query.filter_by(email=email).first()

    if employee:
        return {"error": "Employee already exists"}, 409
    
    hashed_password = generate_password_hash(password)
    new_employee = Employee(email=email, password=hashed_password, role=role, department=department, employee_name=employee_name)

    db.session.add(new_employee)
    db.session.commit()

    EID = new_employee.employee_id
    return {"employee_id": EID, "role": role}, 201

@app.route('/reset', methods=['POST'])
def reset():
    pass

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run()