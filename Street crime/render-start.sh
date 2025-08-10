#!/usr/bin/env bash
exec gunicorn -k eventlet -w 1 app:app --bind 0.0.0.0:$PORT
