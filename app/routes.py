import zipfile
from app import app, db, argon2
from app.models import User, Note, Meta, aes_encrypt, aes_encrypt_old
from flask import render_template, request, jsonify, abort, send_file
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity


@app.route('/api/sign-up', methods=['POST'])
def sign_up():
  if app.config['PREVENT_SIGNUPS']:
    abort(400)

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
@jwt_required()
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

  enc_date = aes_encrypt(title)
  note = user.notes.filter_by(title=enc_date).first()

  if not Note:
    # Check old encryption
    enc_date = aes_encrypt_old(title)
    note = user.notes.filter_by(title=enc_date).first()
  if not note:
    note = Note(user_id=user.uuid, name=title, text=data, is_date=True)
  else:
    note.text = data

  db.session.add(note)
  db.session.flush()
  db.session.commit()

  return jsonify(note=note.serialize), 200


@app.route('/api/create_note', methods=['POST'])
@jwt_required()
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

  note = Note(user_id=user.uuid, text=data)

  db.session.add(note)
  db.session.flush()
  db.session.commit()

  return jsonify(note=note.serialize), 200


@app.route('/api/save_task', methods=['PUT'])
@jwt_required()
def save_task():
  req = request.get_json()
  uuid = req.get('uuid')
  name = req.get('name')

  if not uuid or not name:
    abort(400)

  username = get_jwt_identity()

  if not username:
    abort(401)

  user = User.query.filter_by(username=username.lower()).first()

  if not user:
    abort(400)

  task = user.meta.filter_by(uuid=uuid).first()

  if not task:
    abort(400)

  task.name = name

  db.session.add(task)
  db.session.flush()
  db.session.commit()

  return jsonify({}), 200


@app.route('/api/save_note', methods=['PUT'])
@jwt_required()
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

  note.text = data

  db.session.add(note)
  db.session.flush()
  db.session.commit()

  return jsonify(note=note.serialize), 200


@app.route('/api/delete_note/<uuid>', methods=['DELETE'])
@jwt_required()
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
@jwt_required()
def refresh_jwt():
  username = get_jwt_identity()

  if not username:
    abort(401)

  access_token = create_access_token(identity=username)
  return jsonify(token=access_token), 200


@app.route('/api/note', methods=['GET'])
@jwt_required()
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
@jwt_required()
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
    'data': '---\ntags: \nprojects: \n---\n\n',
    'is_date': True,
    'user_id': user.uuid
  }

  date_enc = aes_encrypt(date)
  note = user.notes.filter_by(title=date_enc, is_date=True).first()

  if not note:
    # Check old encryption
    date_enc = aes_encrypt_old(date)
    note = user.notes.filter_by(title=date_enc, is_date=True).first()

  if note:
    ret_note = note.serialize

  return jsonify(day=ret_note), 200


@app.route('/api/events', methods=['GET'])
@jwt_required()
def cal_events():
  username = get_jwt_identity()
  user = User.query.filter_by(username=username.lower()).first()

  if not user:
    abort(400)

  # TODO: Only do current month or something
  notes = user.notes.filter_by(is_date=True).all()

  return jsonify(events=[x.name for x in notes]), 200


@app.route('/api/sidebar', methods=['GET'])
@jwt_required()
def sidebar_data():
  username = get_jwt_identity()
  user = User.query.filter_by(username=username.lower()).first()

  if not user:
    abort(400)

  notes = sorted([a.serialize for a in user.notes.filter_by(is_date=False).all()], key=lambda note: note['title'].lower())
  tags = sorted(set([a.name for a in user.meta.filter_by(kind="tag").all()]), key=lambda s: s.lower())
  projects = sorted(set([a.name for a in user.meta.filter_by(kind="project").all()]), key=lambda s: s.lower())
  tasks = sorted([a.serialize for a in user.meta.filter_by(kind="task").all()], key=lambda task: task['note_id'])
  auto_save = user.auto_save

  return jsonify(tags=tags,projects=projects,notes=notes,tasks=tasks,auto_save=auto_save), 200


@app.route('/api/toggle_auto_save', methods=['POST'])
@jwt_required()
def toggle_auto_save():
  req = request.get_json()
  auto_save = req.get('auto_save', False)

  username = get_jwt_identity()

  if not username:
    abort(401)

  user = User.query.filter_by(username=username.lower()).first()

  if not user:
    abort(400)

  user.auto_save = auto_save

  db.session.add(user)
  db.session.flush()
  db.session.commit()

  return jsonify({}), 200


@app.route('/api/search', methods=['POST'])
@jwt_required()
def search():
  req = request.get_json()
  selected_search = req.get('selected', '')
  search_string = req.get('search', '')

  if not selected_search or not search_string or not len(search_string) > 0:
    abort(400)

  if selected_search not in ['project', 'tag', 'search']:
    abort(400)

  username = get_jwt_identity()

  if not username:
    abort(401)

  user = User.query.filter_by(username=username.lower()).first()

  if not user:
    abort(400)

  matched_notes = []

  if selected_search == 'project':
    all_projects = user.meta.filter_by(kind="project").all()

    for project in all_projects:
      if search_string.lower() in project.name.lower():
        matched_notes.append(project.note_id)

  elif selected_search == 'tag':
    all_tags = user.meta.filter_by(kind="tag").all()

    for tag in all_tags:
      if search_string.lower() in tag.name.lower():
        matched_notes.append(tag.note_id)

  elif selected_search == 'search':
    all_notes = user.notes.all()

    for note in all_notes:
      if search_string.lower() in note.text.lower():
        matched_notes.append(note.uuid)

  filtered_notes = Note.query.filter(Note.uuid.in_(matched_notes)).all()
  notes = []

  for note in filtered_notes:
    cleaned_note = note.serialize
    cleaned_note['tags'] = sorted(set([x.name for x in note.meta.filter_by(kind="tag").all()]), key=lambda s: s.lower())
    cleaned_note['projects'] = sorted(set([x.name for x in note.meta.filter_by(kind="project").all()]), key=lambda s: s.lower())
    notes.append(cleaned_note)

  sorted_nodes = sorted(notes, key=lambda s: s['title'].lower())

  return jsonify(notes=sorted_nodes), 200


@app.route('/api/export')
@jwt_required()
def export():
  username = get_jwt_identity()
  user = User.query.filter_by(username=username.lower()).first()

  if not user:
    abort(400)

  zf = zipfile.ZipFile('export.zip', mode='w')
  notes = user.notes
  for note in notes:
    ret_note = note.serialize
    zf.writestr(ret_note['title'] + '.md', ret_note['data'], zipfile.ZIP_DEFLATED)
    print(ret_note)
  zf.close()

  return send_file('../export.zip', as_attachment=True)


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
  return render_template("index.html")
