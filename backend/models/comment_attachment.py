from datetime import datetime
from models.extensions import db


class CommentAttachment(db.Model):
    __tablename__ = 'comment_attachments'

    id = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('task_comments.id', ondelete='CASCADE'), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255))
    mime_type = db.Column(db.String(100))
    size = db.Column(db.Integer)
    uploaded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "comment_id": self.comment_id,
            "filename": self.filename,
            "original_name": self.original_name,
            "mime_type": self.mime_type,
            "size": self.size,
            "uploaded_at": (self.uploaded_at.isoformat(timespec="seconds") + "Z") if self.uploaded_at else None,
        }


