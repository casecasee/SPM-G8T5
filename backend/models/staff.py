from werkzeug.security import generate_password_hash, check_password_hash
from models.extensions import db

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