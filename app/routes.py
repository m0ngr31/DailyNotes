from app import app, db, argon2
from app.models import User
from flask import render_template, request, jsonify, abort
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
import frontmatter


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


@app.route('/api/note', methods=['POST'])
@jwt_required
def get_note():
  req = request.get_json()
  username = get_jwt_identity()

  user = User.query.filter_by(username=username).first()

  if not user:
    abort(400)

  print user.notes

  access_token = create_access_token(identity=username)
  return jsonify(access_token=access_token), 200


@app.route('/api/activity', methods=['POST'])
@jwt_required
def month_activity():
  req = request.get_json()
  username = get_jwt_identity()

  # print req

  # data = req.get('data', '')

  # parsed = frontmatter.loads(data)
  # print(parsed)

  access_token = create_access_token(identity=username)
  return jsonify(access_token=access_token), 200


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
  return render_template("index.html")