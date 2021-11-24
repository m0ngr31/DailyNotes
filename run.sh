#!/bin/sh

PUID=${PUID:-911}
PGID=${PGID:-911}

if [ "$(whoami)" = "abc" ]; then
  if [ "$PUID" != 911 ]; then
    echo "Setting container permissions"
    sudo groupmod -o -g "$PGID" abc
    sudo usermod -o -u "$PUID" abc
    sudo chown -R abc:abc /app
  fi
fi

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

exec gunicorn server:app -b 0.0.0.0:5000