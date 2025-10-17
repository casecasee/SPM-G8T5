from models.extensions import db
from datetime import datetime

project_members = db.Table(
    'project_members',
    db.Column('project_id', db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), primary_key=True),
    db.Column('staff_id', db.Integer, db.ForeignKey('staff.employee_id', ondelete='CASCADE'), primary_key=True),
    mysql_engine="InnoDB"
)

class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    owner = db.Column(db.String(255))
    owner_id = db.Column(db.Integer, db.ForeignKey('staff.employee_id', ondelete='SET NULL'), nullable=True, index=True)
    status = db.Column(db.String(50), nullable=False, default='Active')
    tasks_done = db.Column(db.Integer, nullable=False, default=0)
    tasks_total = db.Column(db.Integer, nullable=False, default=0)
    # New: optional project-level due date
    due_date = db.Column(db.DateTime, nullable=True)
    # updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    members = db.relationship('Staff', secondary=project_members, lazy='dynamic')

    def to_dict(self):
        member_objs = self.members.all()
        member_ids = [m.employee_id for m in member_objs]
        member_names = [m.employee_name for m in member_objs]
        return {
            "id": self.id,
            "name": self.name,
            "owner": self.owner,
            "ownerId": self.owner_id,
            "status": self.status,
            "tasksDone": self.tasks_done,
            "tasksTotal": self.tasks_total,
            "dueDate": (self.due_date.isoformat(timespec="milliseconds") + "Z") if self.due_date else None,
            "updatedAt": self.updated_at.isoformat(timespec="milliseconds") + "Z",
            "memberIds": member_ids,
            "memberNames": member_names,
        }