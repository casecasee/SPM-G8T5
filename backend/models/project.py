from models.extensions import db
from datetime import datetime

class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    owner = db.Column(db.String(255))
    status = db.Column(db.String(50), nullable=False, default='Active')  # or ENUM
    tasks_done = db.Column(db.Integer, nullable=False, default=0)
    tasks_total = db.Column(db.Integer, nullable=False, default=0)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "owner": self.owner,
            "status": self.status,
            "tasksDone": self.tasks_done,
            "tasksTotal": self.tasks_total,
            "updatedAt": self.updated_at.isoformat(timespec="milliseconds") + "Z",
        }