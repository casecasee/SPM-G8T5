# backend/tasks/task.py
import os
import time
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from models import db, Task

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/SPM'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads/attachments'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

CORS(app, supports_credentials=True, origins=["http://localhost:5173", "http://localhost:5174"])
db.init_app(app)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Separate upload endpoint
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
        
        # Create upload directory if it doesn't exist
        upload_dir = app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        
        filepath = os.path.join(upload_dir, unique_filename)
        file.save(filepath)
        
        return jsonify({
            'message': 'File uploaded successfully',
            'file_path': filepath,
            'filename': unique_filename
        }), 200
    
    return jsonify({'error': 'Invalid file type'}), 400

# Serve uploaded files
@app.route('/attachments/<path:filename>')
def serve_attachment(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Your existing task routes (GET, POST, PUT, DELETE) go here...
# Make sure to update the POST /tasks route to accept attachment path

@app.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    
    new_task = Task(
        title=data.get('title'),
        description=data.get('description'),
        attachment=data.get('attachment'),  # File path from upload endpoint
        priority=data.get('priority', 5),
        deadline=data.get('deadline'),
        status=data.get('status', 'ongoing'),
        owner=data.get('employee_id'),
        project_id=data.get('project_id'),  # Optional
        parent_id=data.get('parent_id')     # Optional, for subtasks
    )
    
    db.session.add(new_task)
    db.session.commit()
    
    return jsonify(new_task.to_dict()), 201

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5002)