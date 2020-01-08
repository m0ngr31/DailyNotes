from app import db
from app.model_types import GUID
from sqlalchemy.sql import func
import uuid

class User(db.Model):
  uuid = db.Column(GUID, primary_key=True, index=True, unique=True, default=lambda: uuid.uuid4())
  username = db.Column(db.String(64), unique=True, nullable=False)
  password_hash = db.Column(db.String(128), nullable=False)
  notes = db.relationship('Note', backref='user')

  def __repr__(self):
    return '<User {}>'.format(self.uuid)


class Note(db.Model):
  uuid = db.Column(GUID, primary_key=True, index=True, unique=True, default=lambda: uuid.uuid4())
  tags = db.Column(db.String)
  projects = db.Column(db.String)
  user_id = db.Column(GUID, db.ForeignKey('user.uuid'), nullable=False)
  data = db.Column(db.String)
  title = db.Column(db.String(128), nullable=False, unique=True)
  date = db.Column(db.DateTime(timezone=True), server_default=func.now())
  is_date = db.Column(db.Boolean, default=False)

  def __repr__(self):
    return '<Note {}>'.format(self.uuid)
