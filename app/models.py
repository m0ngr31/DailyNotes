from app import app, db
from app.model_types import GUID
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy import event
from Crypto.Cipher import AES
import binascii
import uuid
import frontmatter
import re


key = app.config['DB_ENCRYPTION_KEY']


def aes_encrypt(data):
  cipher = AES.new(key)
  data = data + (" " * (16 - (len(data) % 16)))
  return binascii.hexlify(cipher.encrypt(data))

def aes_decrypt(data):
  try:
    cipher = AES.new(key)
    return cipher.decrypt(binascii.unhexlify(data)).rstrip()
  except:
    # If data is not encrypted, just return it
    return data


class User(db.Model):
  uuid = db.Column(GUID, primary_key=True, index=True, unique=True, default=lambda: uuid.uuid4())
  username = db.Column(db.String(64), unique=True, nullable=False)
  password_hash = db.Column(db.String(128), nullable=False)
  notes = db.relationship('Note', lazy='dynamic', cascade='all, delete, delete-orphan')
  tags = db.relationship('Tag', lazy='dynamic', cascade='all, delete, delete-orphan')
  projects = db.relationship('Project', lazy='dynamic', cascade='all, delete, delete-orphan')
  tasks = db.relationship('Task', lazy='dynamic', cascade='all, delete, delete-orphan')

  def __repr__(self):
    return '<User {}>'.format(self.uuid)


class Tag(db.Model):
  uuid = db.Column(GUID, primary_key=True, index=True, unique=True, default=lambda: uuid.uuid4())
  user_id = db.Column(GUID, db.ForeignKey('user.uuid'), nullable=False)
  note_id = db.Column(GUID, db.ForeignKey('note.uuid'), nullable=False)
  name = db.Column(db.String)

  def __repr__(self):
    return '<Tag {}>'.format(self.uuid)


class Project(db.Model):
  uuid = db.Column(GUID, primary_key=True, index=True, unique=True, default=lambda: uuid.uuid4())
  user_id = db.Column(GUID, db.ForeignKey('user.uuid'), nullable=False)
  note_id = db.Column(GUID, db.ForeignKey('note.uuid'), nullable=False)
  name = db.Column(db.String)

  def __repr__(self):
    return '<Project {}>'.format(self.uuid)


class Task(db.Model):
  uuid = db.Column(GUID, primary_key=True, index=True, unique=True, default=lambda: uuid.uuid4())
  user_id = db.Column(GUID, db.ForeignKey('user.uuid'), nullable=False)
  note_id = db.Column(GUID, db.ForeignKey('note.uuid'), nullable=False)
  name = db.Column(db.String)
  swimlane = db.Column(db.String)

  def __repr__(self):
    return '<Task {}>'.format(self.uuid)


class Note(db.Model):
  uuid = db.Column(GUID, primary_key=True, index=True, unique=True, default=lambda: uuid.uuid4())
  user_id = db.Column(GUID, db.ForeignKey('user.uuid'), nullable=False)
  data = db.Column(db.String)
  title = db.Column(db.String(128), nullable=False, unique=True)
  date = db.Column(db.DateTime(timezone=True), server_default=func.now())
  is_date = db.Column(db.Boolean, default=False)
  tags = db.relationship('Tag', lazy='dynamic', cascade='all, delete, delete-orphan')
  projects = db.relationship('Project', lazy='dynamic', cascade='all, delete, delete-orphan')
  tasks = db.relationship('Task', lazy='dynamic', cascade='all, delete, delete-orphan')

  @hybrid_property
  def text(self):
    return aes_decrypt(self.data)

  @text.setter
  def text(self, value):
    self.data = aes_encrypt(value)

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


# Update title automatically
def before_change_note(mapper, connection, target):
  title = None

  data = frontmatter.loads(target.text)

  if isinstance(data.get('title'), str) and len(data.get('title')) > 0:
    title = data.get('title')

  if title and not target.is_date:
    target.title = title


# Handle changes to tasks, projects, and tags
def after_change_note(mapper, connection, target):
  tags = []
  projects = []
  # tasks = []

  data = frontmatter.loads(target.text)

  if isinstance(data.get('tags'), list):
    tags = list(set([x.replace(',', '\,') for x in data.get('tags')]))
  elif isinstance(data.get('tags'), str):
    tags = list(set(map(str.strip, data['tags'].split(','))))

  if isinstance(data.get('projects'), list):
    projects = list(set([x.replace(',', '\,') for x in data.get('projects')]))
  elif isinstance(data.get('projects'), str):
    projects = list(set(map(str.strip, data['projects'].split(','))))

  # Parse out tasks here #

  existing_tags = Tag.query.filter_by(note_id=target.uuid).all()
  existing_projects = Project.query.filter_by(note_id=target.uuid).all()
  # existing_tasks = Task.query.filter_by(note_id=target.uuid).all()

  for tag in existing_tags:
    if tag.name not in tags:
      connection.execute(
        'DELETE FROM tag WHERE uuid = (?)',
        '{}'.format(tag.uuid).replace('-', '')
      )
    else:
      tags.remove(tag.name)

  for tag in tags:
    connection.execute(
      'INSERT INTO tag (uuid, user_id, note_id, name) VALUES (?, ?, ?, ?)',
      '{}'.format(uuid.uuid4()).replace('-', ''),
      '{}'.format(target.user_id).replace('-', ''),
      '{}'.format(target.uuid).replace('-', ''),
      tag
    )

  for project in existing_projects:
    if project.name not in projects:
      connection.execute(
        'DELETE FROM project WHERE uuid = (?)',
        '{}'.format(project.uuid).replace('-', '')
      )
    else:
      projects.remove(project.name)

  for project in projects:
    connection.execute(
      'INSERT INTO project (uuid, user_id, note_id, name) VALUES (?, ?, ?, ?)',
      '{}'.format(uuid.uuid4()).replace('-', ''),
      '{}'.format(target.user_id).replace('-', ''),
      '{}'.format(target.uuid).replace('-', ''),
      project
    )


event.listen(Note, 'before_insert', before_change_note)
event.listen(Note, 'before_update', before_change_note)
event.listen(Note, 'after_insert', after_change_note)
event.listen(Note, 'after_update', after_change_note)