#!/bin/sh

./verify_env.py

if test -f "./config/.env"; then
  source ./config/.env
fi

export FLASK_APP=server.py

flask db upgrade

exec gunicorn server:app -b 0.0.0.0:5000