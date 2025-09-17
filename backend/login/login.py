from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy 
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/SPM'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # suppress warning msgs
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299} # do not timeout

db = SQLAlchemy(app) # initialise connection to db

class User(db.Model):
    __tablename__ = 'User'
    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)

@app.route('/login', methods=['POST'])
def login():
    # input: {email:str, password:str}

    data = request.json
    email = data.get('email')
    password = data.get('password')
    user = User.query.filter_by(email=email).first()
    if not user:
        return {"error": "User does not exist"}, 404
    if not check_password_hash(user.password, password):
        return {"error": "Incorrect password"}, 401
    UID = user.user_id
    role = user.role

    return {"user_id": UID, "role": role}

@app.route('/register', methods=['POST'])
def register():
    
    # input: {email:str, password:str, role:str}
    # check if user already exists in database
    # if exists, return error
    # if does not exist, create new user and return user_id and role
    data = request.json
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')
    user = User.query.filter_by(email=email).first()
    if user:
        return {"error": "User already exists"}, 409
    hashed_password = generate_password_hash(password, method='scrypt', salt_length=16)
    new_user = User(email=email, password=hashed_password, role=role)
    db.session.add(new_user)
    db.session.commit()
    UID = new_user.user_id
    return {"user_id": UID, "role": role}, 201

@app.route('/reset', methods=['POST'])
def reset():
    pass

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run()