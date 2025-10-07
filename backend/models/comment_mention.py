from models.extensions import db


class CommentMention(db.Model):
    __tablename__ = 'comment_mentions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('task_comments.id', ondelete='CASCADE'), nullable=False, index=True)
    mentioned_id = db.Column(db.Integer, db.ForeignKey('staff.employee_id', ondelete='CASCADE'), nullable=False, index=True)


