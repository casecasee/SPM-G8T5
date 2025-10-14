from flask import Flask, request, jsonify, session
from flask_cors import CORS, cross_origin
from flask_socketio import SocketIO, emit, join_room
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import uuid

from models.extensions import db
from models.notification import Notification, NotificationPreferences, DeadlineNotificationLog

app = Flask(__name__)
app.secret_key = "issa_secret_key"
app.config["SESSION_COOKIE_SAMESITE"] = "None"
app.config["SESSION_COOKIE_SECURE"] = True

# Update CORS configuration
CORS(app, 
     resources={r"/api/*": {
         "origins": ["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173"],
         "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
         "allow_headers": ["Content-Type", "X-Employee-Id", "Authorization"],
         "supports_credentials": True,
         "expose_headers": ["Content-Type"]
     }})

socketio = SocketIO(app, 
                   cors_allowed_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173"],
                   async_mode='threading',
                   logger=False,
                   engineio_logger=False)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/SPM'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

db.init_app(app)

# Service URLs
EMPLOYEE_SERVICE_URL = "http://localhost:5000"
TASK_SERVICE_URL = "http://localhost:5002"  # Your tasks run on 5002
PROJECT_SERVICE_URL = "http://localhost:5001"  # Assuming projects on 5001

# ... rest of the notification service code from the artifact
# (Copy the NotificationService class and all routes)

# Add OPTIONS handler for CORS preflight
@app.route('/api/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    """Handle CORS preflight requests"""
    response = jsonify({'status': 'ok'})
    response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', '*'))
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,X-Employee-Id,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,PATCH,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response, 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    socketio.run(app, debug=True, port=5003)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    socketio.run(app, debug=True, port=5003)