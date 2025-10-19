from models.extensions import db

Task_Collaborators = db.Table(
    'task_collaborators',
    db.Column('task_id', db.Integer, db.ForeignKey('task.task_id', ondelete='CASCADE'), primary_key=True),
    db.Column('staff_id', db.Integer, db.ForeignKey('staff.employee_id', ondelete='CASCADE'), primary_key=True),
    mysql_engine="InnoDB"
)

class Task(db.Model):
    __tablename__ = 'task'

    task_id        = db.Column(db.Integer, primary_key=True)
    title          = db.Column(db.String(255), nullable=False)
    description    = db.Column(db.Text, nullable=False)
    attachment     = db.Column(db.String(512), nullable=True) # TODO: aws s3 link
    priority       = db.Column(db.Integer, nullable=True)  # 1-10
    recurrence    = db.Column(db.Integer, nullable=True)  # in days, for recurring tasks, daily=1, weekly=7, monthly=30

    # dates / status
    start_date     = db.Column(db.DateTime, nullable=True) # TODO: logic for setting start_date when status changes to IN_PROGRESS
    deadline       = db.Column(db.DateTime, nullable=True, index=True)
    completed_date = db.Column(db.DateTime, nullable=True) # TODO: logic for setting completed_date when status changes to DONE
    created_at     = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    status         = db.Column(db.String(32), nullable=False)

    # owner & project (FKs to other services' tables)
    owner          = db.Column(db.Integer, db.ForeignKey('staff.employee_id', ondelete='RESTRICT'), nullable=False, index=True)
    project_id     = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True, index=True)

    # self-referential unary relationship for one-level subtasks
    parent_id      = db.Column(db.Integer, db.ForeignKey('task.task_id', ondelete='CASCADE'), nullable=True)

    # relationship wiring: parent <-> subtasks
    parent   = db.relationship('Task',
                               remote_side=[task_id],
                               backref=db.backref('subtasks', cascade='all, delete-orphan', lazy='dynamic'),
                               foreign_keys=[parent_id],
                               passive_deletes=True)
    
    # staff owner relationship
    owner_staff = db.relationship(
        'Staff',
        foreign_keys=[owner],
        backref='owned_tasks'
    )

    # collaborators many-to-many
    collaborators = db.relationship(
    'Staff',
    secondary=Task_Collaborators, 
    lazy='dynamic'
)

    # comments relationship
    comments = db.relationship(
        'Comment',
        backref='task',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    # __table_args__ = (
        # prevent self-loop: a task cannot be its own parent
        # CheckConstraint('parent_id IS NULL OR parent_id <> task_id', name='ck_task_no_self_parent'),)
    
    def __init__(self, title, description, deadline, status, owner, collaborators, priority, start_date=None, attachment=None, project_id=None, completed_date=None, parent_id=None, recurrence=None):
        self.title = title
        self.description = description
        self.deadline = deadline
        self.status = status
        self.owner = owner
        self.start_date = start_date
        self.priority = priority
        self.attachment = attachment 
        self.project_id = project_id
        self.completed_date = completed_date 
        self.parent_id = parent_id
        self.collaborators = collaborators
        self.recurrence = recurrence

    # TODO: one layer of subtasks only

    def to_dict(self):
        # print(self.subtasks.all())
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "attachment": self.attachment,
            "deadline": self.deadline.isoformat(),
            "status": self.status,
            "owner": self.owner,
            "project_id": self.project_id,
            "parent_id": self.parent_id,
            "priority": self.priority,
            "collaborators": [collaborator.employee_id for collaborator in self.collaborators],
            "subtasks": [subtask.to_dict() for subtask in self.subtasks.all()],
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "completed_date": self.completed_date.isoformat() if self.completed_date else None,
            "created_at": self.created_at.isoformat(),
            "recurrence": self.recurrence
        }


