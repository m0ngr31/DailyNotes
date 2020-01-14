from app import app, db, argon2
from app.models import User, Note
from flask import render_template, request, jsonify, abort
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
import itertools
import re


@app.route('/api/sign-up', methods=['POST'])
def sign_up():
  req = request.get_json()
  username = req.get('username')
  password = req.get('password')

  if not username or not password:
    abort(400)

  password_hash = argon2.generate_password_hash(password)

  new_user = User(username=username.lower(), password_hash=password_hash)
  db.session.add(new_user)
  db.session.commit()

  access_token = create_access_token(identity=username)
  return jsonify(access_token=access_token), 200


@app.route('/api/login', methods=['POST'])
def login():
  req = request.get_json()
  username = req.get('username')
  password = req.get('password')

  if not username or not password:
    abort(400)

  user = User.query.filter_by(username=username.lower()).first()

  if not user:
    return jsonify({"msg": "Bad username or password"}), 401

  if not argon2.check_password_hash(user.password_hash, password):
    return jsonify({"msg": "Bad username or password"}), 401

  access_token = create_access_token(identity=username)
  return jsonify(access_token=access_token), 200


@app.route('/api/save_day', methods=['PUT'])
@jwt_required
def save_day():
  req = request.get_json()
  title = req.get('title')
  data = req.get('data', '')

  if not title:
    abort(400)

  username = get_jwt_identity()

  if not username:
    abort(401)

  user = User.query.filter_by(username=username.lower()).first()

  if not user:
    abort(400)

  note = user.notes.filter_by(title=title).first()

  if not note:
    note = Note(user_id=user.uuid, title=title, data=data, is_date=True)
  else:
    note.data = data

  db.session.add(note)
  db.session.flush()
  db.session.commit()

  return jsonify(note=note.serialize), 200


@app.route('/api/create_note', methods=['POST'])
@jwt_required
def create_note():
  req = request.get_json()
  data = req.get('data', '')

  if not data:
    abort(400)

  username = get_jwt_identity()

  if not username:
    abort(401)

  user = User.query.filter_by(username=username.lower()).first()

  if not user:
    abort(400)

  note = Note(user_id=user.uuid, data=data)

  db.session.add(note)
  db.session.flush()
  db.session.commit()

  return jsonify(note=note.serialize), 200


@app.route('/api/save_note', methods=['PUT'])
@jwt_required
def save_note():
  req = request.get_json()
  uuid = req.get('uuid')
  data = req.get('data', '')

  if not uuid:
    abort(400)

  username = get_jwt_identity()

  if not username:
    abort(401)

  user = User.query.filter_by(username=username.lower()).first()

  if not user:
    abort(400)

  note = user.notes.filter_by(uuid=uuid).first()

  if not note:
    abort(400)

  note.data = data

  db.session.add(note)
  db.session.flush()
  db.session.commit()

  return jsonify(note=note.serialize), 200


@app.route('/api/delete_note/<uuid>', methods=['DELETE'])
@jwt_required
def delete_note(uuid):
  if not uuid:
    abort(400)

  username = get_jwt_identity()

  if not username:
    abort(401)

  user = User.query.filter_by(username=username.lower()).first()

  if not user:
    abort(400)

  note = user.notes.filter_by(uuid=uuid).first()

  if not note:
    abort(400)

  db.session.delete(note)
  db.session.commit()

  return jsonify({}), 200  


@app.route('/api/refresh_jwt', methods=['GET'])
@jwt_required
def refresh_jwt():
  username = get_jwt_identity()

  if not username:
    abort(401)

  access_token = create_access_token(identity=username)
  return jsonify(token=access_token), 200


@app.route('/api/note', methods=['GET'])
@jwt_required
def get_note():
  uuid = request.args.get('uuid')
  
  if not uuid:
    abort(400)

  username = get_jwt_identity()
  user = User.query.filter_by(username=username.lower()).first()

  if not user:
    abort(400)

  note = user.notes.filter_by(uuid=uuid).first()

  if not note:
    abort(400)

  return jsonify(note=note.serialize), 200


@app.route('/api/date', methods=['GET'])
@jwt_required
def get_date():
  date = request.args.get('date')

  if not date:
    abort(400)

  username = get_jwt_identity()
  user = User.query.filter_by(username=username.lower()).first()

  if not user:
    abort(400)

  ret_note = {
    'title': date,
    'data': '---\ntags:\nprojects:\n---\n\n',
    'is_date': True,
    'user_id': user.uuid
  }

  note = user.notes.filter_by(title=date, is_date=True).first()
  
  if note:
    ret_note = note.serialize

  return jsonify(day=ret_note), 200


@app.route('/api/events', methods=['GET'])
@jwt_required
def cal_events():
  username = get_jwt_identity()
  user = User.query.filter_by(username=username.lower()).first()

  if not user:
    abort(400)

  # TODO: Only do current month or something
  notes = user.notes.filter_by(is_date=True)

  return jsonify(events=[x.title for x in notes]), 200


@app.route('/api/sidebar', methods=['GET'])
@jwt_required
def sidebar_data():
  username = get_jwt_identity()
  user = User.query.filter_by(username=username.lower()).first()

  if not user:
    abort(400)

  notes_all = user.notes.all()

  tags = []
  projects = []
  notes = []
  all_notes = []

  for note in notes_all:
    serialized_note = note.serialize_full

    tags.extend(serialized_note['tags'])
    projects.extend(serialized_note['projects'])

    all_notes.append({
      'title': note.title,
      'uuid': note.uuid,
      'data': note.data,
      'is_date': note.is_date,
      'tags': serialized_note['tags'],
      'projects': serialized_note['projects'],
    })

    if not note.is_date:
      notes.append({
        'title': note.title,
        'uuid': note.uuid,
      })

  notes = sorted(notes, key=lambda note: note['title'].lower())
  tags = sorted([x for x in list(set(tags))], key=lambda name: name.lower())
  projects = sorted([x for x in list(set(projects))], key=lambda name: name.lower())

  return jsonify(tags=tags,projects=projects,notes=notes,notes_all=all_notes), 200


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
  return render_template("index.html")