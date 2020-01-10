from app import app, db, argon2
from app.models import User, Note
from flask import render_template, request, jsonify, abort
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
import itertools


@app.route('/api/sign-up', methods=['POST'])
def sign_up():
  req = request.get_json()
  username = req.get('username')
  password = req.get('password')

  if not username or not password:
    abort(400)

  password_hash = argon2.generate_password_hash(password)

  new_user = User(username=username, password_hash=password_hash)
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

  user = User.query.filter_by(username=username).first()

  if not user:
    return jsonify({"msg": "Bad username or password"}), 401

  if not argon2.check_password_hash(user.password_hash, password):
    return jsonify({"msg": "Bad username or password"}), 401

  access_token = create_access_token(identity=username)
  return jsonify(access_token=access_token), 200


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
  user = User.query.filter_by(username=username).first()

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
  user = User.query.filter_by(username=username).first()

  if not user:
    abort(400)

  ret_note = {
    'title': date,
    'data': '---\ndate: {}\n---\n\n'.format(date),
    'is_date': True,
    'user_id': user.uuid
  }

  note = user.notes.filter_by(title=date).first()
  
  if note:
    ret_note = note.serialize

  return jsonify(day=ret_note), 200


@app.route('/api/events', methods=['GET'])
@jwt_required
def cal_events():
  username = get_jwt_identity()
  user = User.query.filter_by(username=username).first()

  if not user:
    abort(400)

  # TODO: Only do current month or something
  notes = user.notes.filter_by(is_date=True)

  return jsonify(events=[x.date for x in notes]), 200


@app.route('/api/sidebar', methods=['GET'])
@jwt_required
def sidebar_data():
  username = get_jwt_identity()
  user = User.query.filter_by(username=username).first()

  if not user:
    abort(400)

  notes_all = user.notes.all()
  notes = user.notes.filter_by(is_date=False)

  tags = [x for x in list(set(itertools.chain(*[(item.tags or '').split(',') for item in notes_all]))) if x]
  projects = [x for x in list(set(itertools.chain(*[(item.projects or '').split(',') for item in notes_all]))) if x]

  return jsonify(tags=tags,projects=projects,notes=[note.serialize for note in notes]), 200


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
  return render_template("index.html")