# Street Crime Inc - Full Project (All Files Included)

This package contains a full Flask + Socket.IO application with Redis token auth for admin sockets,
audit logging, sample accounts, and templates + static files. It is ready to unzip and push
to a Git repository for deployment to Render (Web Service).

Quick start (local):
1. python -m venv venv
2. source venv/bin/activate  (or venv\Scripts\activate on Windows)
3. pip install -r requirements.txt
4. copy .env.example to .env and adjust as needed
5. python init_db.py
6. ./render-start.sh  (or python app.py for dev)

Sample accounts created by init_db.py / app.py on first run:
- admin / adminpass
- mod / modpass
- help / helppass
- player1 / player1
- player2 / player2
