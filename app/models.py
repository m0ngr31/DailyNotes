from app import db
from app.model_types import GUID
from sqlalchemy.sql import func
from sqlalchemy import event
import uuid
import frontmatter
import re


class User(db.Model):
  uuid = db.Column(GUID, primary_key=True, index=True, unique=True, default=lambda: uuid.uuid4())
  username = db.Column(db.String(64), unique=True, nullable=False)
  password_hash = db.Column(db.String(128), nullable=False)
  notes = db.relationship('Note', lazy='dynamic')

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

  @property
  def serialize(self):
    return {
      'uuid': self.uuid,
      'data': self.data,
      'title': self.title,
      'date': self.date,
      'is_date': self.is_date,
    }

  @property
  def serialize_full(self):
    return {
      'uuid': self.uuid,
      'data': self.data,
      'title': self.title,
      'date': self.date,
      'is_date': self.is_date,
      'tags': [x.replace('\,', ',') for x in list(set(re.split(r'(?<!\\),', (self.tags or '')))) if x],
      'projects': [x.replace('\,', ',') for x in list(set(re.split(r'(?<!\\),', (self.projects or '')))) if x],
    }


def before_change_note(mapper, connection, target):
  tags = ''
  projects = ''
  title = None

  data = frontmatter.loads(target.data)

  if isinstance(data.get('tags'), list):
    tags = ','.join(set([x.replace(',', '\,') for x in data.get('tags')]))
  elif isinstance(data.get('tags'), str):
    tags = ','.join(set(map(str.strip, data['tags'].split(','))))

  if isinstance(data.get('projects'), list):
    projects = ','.join(set([x.replace(',', '\,') for x in data.get('projects')]))
  elif isinstance(data.get('projects'), str):
    projects = ','.join(set(map(str.strip, data['projects'].split(','))))

  if isinstance(data.get('title'), str) and len(data.get('title')) > 0:
    title = data.get('title')
  
  target.tags = tags
  target.projects = projects

  if title and not target.is_date:
    target.title = title


event.listen(Note, 'before_insert', before_change_note)
event.listen(Note, 'before_update', before_change_note)