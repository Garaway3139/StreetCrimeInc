#!/usr/bin/env bash
set -e
echo "Starting services..."
docker-compose up -d
export DATABASE_URL="postgresql://sc_user:sc_pass@localhost:5432/sc_db"
export REDIS_URL="redis://localhost:6379/0"
export SECRET_KEY="change-me-locally"
echo "Initializing DB..."
python init_db.py
echo "Done. Run 'python app.py' or './render-start.sh' to start the server."
