#!/bin/sh

if test -f "./config/.env"; then
  . ./config/.env
fi

./verify_env.py

if test -f "./config/.env"; then
  . ./config/.env
fi

export FLASK_APP=server.py

flask db upgrade

./verify_data_migrations.py

exec gunicorn server:app -b 0.0.0.0:5001
