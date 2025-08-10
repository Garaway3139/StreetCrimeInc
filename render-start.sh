#!/usr/bin/env bash
APP_FILE=$(find . -type f \( -name "app.py" -o -name "main.py" -o -name "server.py" \) | head -n 1)
if [ -z "$APP_FILE" ]; then
  echo "No app file found (app.py/main.py/server.py)"
  exit 1
fi
APP_DIR=$(dirname "$APP_FILE")
APP_NAME=$(basename "$APP_FILE" .py)
cd "$APP_DIR" || exit 1
echo "Starting $APP_NAME from $APP_DIR"
exec gunicorn -k eventlet -w 1 "${APP_NAME}:app" --bind 0.0.0.0:$PORT --log-level info
