from datetime import datetime
from models.extensions import db


class Comment(db.Model):
    __tablename__ = 'task_comments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.task_id', ondelete='CASCADE'), nullable=False, index=True)
    author_id = db.Column(db.Integer, db.ForeignKey('staff.employee_id', ondelete='CASCADE'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "task_id": self.task_id,
            "author_id": self.author_id,
            "content": self.content,
            "created_at": (self.created_at.isoformat(timespec="seconds") + "Z") if self.created_at else None,
            "updated_at": (self.updated_at.isoformat(timespec="seconds") + "Z") if self.updated_at else None,
        }


