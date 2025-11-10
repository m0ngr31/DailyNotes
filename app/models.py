from app import app, db
from app.model_types import GUID
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import event, text
from sqlalchemy.orm.attributes import InstrumentedAttribute
from Crypto.Cipher import AES
import binascii
import uuid
import frontmatter
import re


key = app.config['DB_ENCRYPTION_KEY']

# Ensure key is bytes
if isinstance(key, str):
  key = key.encode('utf-8')

# Pad or truncate key to 32 bytes for AES-256
key = (key + b'\0' * 32)[:32]

# Derive IV from key - must be exactly 16 bytes
iv = key[:16]


def aes_encrypt(data):
  # Ensure data is bytes
  if isinstance(data, str):
    data = data.encode('utf-8')

  cipher = AES.new(key, AES.MODE_CFB, iv)
  return cipher.encrypt(data)

def aes_encrypt_old(data):
  # Ensure data is bytes
  if isinstance(data, str):
    data = data.encode('utf-8')

  cipher = AES.new(key, AES.MODE_ECB)
  data = data + (b" " * (16 - (len(data) % 16)))
  return binascii.hexlify(cipher.encrypt(data))

def aes_decrypt(data):
  # From a new object
  if type(data) is InstrumentedAttribute:
    return ''

  # Ensure data is bytes
  if isinstance(data, str):
    data = data.encode('utf-8')

  cipher = AES.new(key, AES.MODE_CFB, iv)

  decrypted = cipher.decrypt(data)

  try:
    return decrypted.decode('utf-8')
  except:
    # Data is in old encryption or it is unencrypted
    return aes_decrypt_old(data)

def aes_decrypt_old(data):
  try:
    # Ensure data is bytes for unhexlify
    if isinstance(data, str):
      data = data.encode('utf-8')

    cipher = AES.new(key, AES.MODE_ECB)
    return cipher.decrypt(binascii.unhexlify(data)).rstrip().decode('ascii')
  except:
    # If data is not encrypted, just return it
    if isinstance(data, bytes):
      try:
        return data.decode('utf-8')
      except:
        pass
    return data


class User(db.Model):
  uuid = db.Column(GUID, primary_key=True, index=True, unique=True, default=lambda: uuid.uuid4())
  username = db.Column(db.String(64), unique=True, nullable=False)
  password_hash = db.Column(db.String(128), nullable=False)
  auto_save = db.Column(db.Boolean, nullable=True)
  notes = db.relationship('Note', lazy='dynamic', cascade='all, delete, delete-orphan')
  meta = db.relationship('Meta', lazy='dynamic', cascade='all, delete, delete-orphan')

  def __repr__(self):
    return '<User {}>'.format(self.uuid)


class Meta(db.Model):
  uuid = db.Column(GUID, primary_key=True, index=True, unique=True, default=lambda: uuid.uuid4())
  user_id = db.Column(GUID, db.ForeignKey('user.uuid'), nullable=False)
  note_id = db.Column(GUID, db.ForeignKey('note.uuid'), nullable=False)
  name_encrypted = db.Column('name', db.String)
  name_compare = db.Column(db.String)
  kind = db.Column(db.String)

  @hybrid_property
  def name(self):
    return aes_decrypt(self.name_encrypted)

  @name.setter
  def name(self, value):
    self.name_encrypted = aes_encrypt(value)

  def __repr__(self):
    return '<Meta {}>'.format(self.uuid)

  @property
  def serialize(self):
    return {
      'uuid': self.uuid,
      'name': self.name,
      'kind': self.kind,
      'note_id': self.note_id,
    }


class Note(db.Model):
  uuid = db.Column(GUID, primary_key=True, index=True, unique=True, default=lambda: uuid.uuid4())
  user_id = db.Column(GUID, db.ForeignKey('user.uuid'), nullable=False)
  data = db.Column(db.String)
  title = db.Column(db.String(128), nullable=False)
  date = db.Column(db.DateTime(timezone=True), server_default=func.now())
  is_date = db.Column(db.Boolean, default=False)
  meta = db.relationship('Meta', lazy='dynamic', cascade='all, delete, delete-orphan')

  @hybrid_property
  def text(self):
    return aes_decrypt(self.data)

  @text.setter
  def text(self, value):
    self.data = aes_encrypt(value)

  @hybrid_property
  def name(self):
   return aes_decrypt(self.title)

  @name.setter
  def name(self, value):
    self.title = aes_encrypt(value)

  def __repr__(self):
    return '<Note {}>'.format(self.uuid)

  @property
  def serialize(self):
    return {
      'uuid': self.uuid,
      'data': self.text,
      'title': self.name,
      'date': self.date,
      'is_date': self.is_date,
    }


# Update title automatically
def before_change_note(mapper, connection, target):
  title = None

  data = frontmatter.loads(target.text)

  if isinstance(data.get('title'), str) and len(data.get('title')) > 0:
    title = data.get('title')

  if not target.is_date:
    # If no title found in frontmatter, generate a default title
    if not title:
      # Try to extract first line of content as title
      content_lines = data.content.strip().split('\n')
      first_line = ''
      for line in content_lines:
        if line.strip():
          first_line = line.strip()
          break

      if first_line:
        # Remove markdown formatting from first line
        title = first_line.lstrip('#').strip()
        # Limit title length
        if len(title) > 100:
          title = title[:100] + '...'

      # If still no title, use default
      if not title:
        title = 'Untitled Note'

    target.name = title


# Handle changes to tasks, projects, and tags
def after_change_note(mapper, connection, target):
  tags = []
  projects = []

  data = frontmatter.loads(target.text)

  if isinstance(data.get('tags'), list):
    tags = list(set([x.replace(',', '\,') for x in data.get('tags')]))
  elif isinstance(data.get('tags'), str):
    tags = list(set(map(str.strip, data['tags'].split(','))))
  tags = [x for x in tags if x]

  if isinstance(data.get('projects'), list):
    projects = list(set([x.replace(',', '\,') for x in data.get('projects')]))
  elif isinstance(data.get('projects'), str):
    projects = list(set(map(str.strip, data['projects'].split(','))))
  projects = [x for x in projects if x]

  tasks = re.findall("- \[[x| ]\] .*$", data.content, re.MULTILINE)

  existing_tags = []
  existing_projects = []
  existing_tasks = []

  metas = Meta.query.filter_by(note_id=target.uuid).all()

  for meta in metas:
    if meta.kind == 'tag':
      existing_tags.append(meta)
    elif meta.kind == 'project':
      existing_projects.append(meta)
    elif meta.kind == 'task':
      existing_tasks.append(meta)

  for tag in existing_tags:
    if tag.name not in tags:
      connection.execute(
        text('DELETE FROM meta WHERE uuid = :uuid'),
        {'uuid': '{}'.format(tag.uuid).replace('-', '')}
      )
    else:
      tags.remove(tag.name)

  for tag in tags:
    connection.execute(
      text('INSERT INTO meta (uuid, user_id, note_id, name, kind) VALUES (:uuid, :user_id, :note_id, :name, :kind)'),
      {
        'uuid': '{}'.format(uuid.uuid4()).replace('-', ''),
        'user_id': '{}'.format(target.user_id).replace('-', ''),
        'note_id': '{}'.format(target.uuid).replace('-', ''),
        'name': aes_encrypt(tag),
        'kind': 'tag'
      }
    )

  for project in existing_projects:
    if project.name not in projects:
      connection.execute(
        text('DELETE FROM meta WHERE uuid = :uuid'),
        {'uuid': '{}'.format(project.uuid).replace('-', '')}
      )
    else:
      projects.remove(project.name)

  for project in projects:
    connection.execute(
      text('INSERT INTO meta (uuid, user_id, note_id, name, kind) VALUES (:uuid, :user_id, :note_id, :name, :kind)'),
      {
        'uuid': '{}'.format(uuid.uuid4()).replace('-', ''),
        'user_id': '{}'.format(target.user_id).replace('-', ''),
        'note_id': '{}'.format(target.uuid).replace('-', ''),
        'name': aes_encrypt(project),
        'kind': 'project'
      }
    )

  for task in existing_tasks:
    if task.name not in tasks:
      connection.execute(
        text('DELETE FROM meta WHERE uuid = :uuid'),
        {'uuid': '{}'.format(task.uuid).replace('-', '')}
      )
    else:
      tasks.remove(task.name)

  for task in tasks:
    encrypted_task = aes_encrypt(task)

    connection.execute(
      text('INSERT INTO meta (uuid, user_id, note_id, name, name_compare, kind) VALUES (:uuid, :user_id, :note_id, :name, :name_compare, :kind)'),
      {
        'uuid': '{}'.format(uuid.uuid4()).replace('-', ''),
        'user_id': '{}'.format(target.user_id).replace('-', ''),
        'note_id': '{}'.format(target.uuid).replace('-', ''),
        'name': encrypted_task,
        'name_compare': encrypted_task,
        'kind': 'task'
      }
    )

def before_update_task(mapper, connection, target):
  if target.kind != 'task':
    return

  if target.name_encrypted == target.name_compare:
    return

  note = Note.query.get(target.note_id)

  if not note:
    return

  note_data = aes_encrypt(note.text.replace(aes_decrypt(target.name_compare), target.name))

  connection.execute(
    text('UPDATE note SET data = :data WHERE uuid = :uuid'),
    {
      'data': note_data,
      'uuid': '{}'.format(note.uuid).replace('-', '')
    }
  )

  target.name_compare = target.name_encrypted


event.listen(Note, 'before_insert', before_change_note)
event.listen(Note, 'before_update', before_change_note)
event.listen(Note, 'after_insert', after_change_note)
event.listen(Note, 'after_update', after_change_note)
event.listen(Meta, 'before_update', before_update_task)
