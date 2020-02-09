#!/usr/bin/env python

from app import app, db
from app.models import Note, Meta

# Setup Flask context
ctx = app.test_request_context()
ctx.push()

def main():
  needs_migration = False

  first_note = Note.query.first()
  meta = Meta.query.first()

  if meta or not first_note or first_note.text is not first_note.data:
    return

  # Notes need to be migrated
  notes = Note.query.all()

  for note in notes:
    # Trigger a change
    note.text = note.data + ''
    note.name = note.title + ''
    db.session.add(note)

  db.session.commit()

main()
