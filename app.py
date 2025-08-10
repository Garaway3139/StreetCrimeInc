import os, secrets, datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from flask_socketio import SocketIO, emit, join_room
from redis import Redis
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret')
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://sc_user:sc_pass@localhost:5432/sc_db')
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

socketio = SocketIO(app, cors_allowed_origins='*', async_mode='eventlet', message_queue=REDIS_URL)
redis_client = Redis.from_url(REDIS_URL, decode_responses=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(30), default='player')
    cash = db.Column(db.Float, default=250.0)
    rep = db.Column(db.Integer, default=0)
    rank_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def set_password(self, pw):
        self.password_hash = bcrypt.generate_password_hash(pw).decode()

    def check_password(self, pw):
        return bcrypt.check_password_hash(self.password_hash, pw)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    text = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    target_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    action = db.Column(db.String(200))
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class AuthUser(UserMixin):
    def __init__(self, user):
        self.id = str(user.id)
        self.username = user.username
        self.role = user.role

@login_manager.user_loader
def load_user(user_id):
    u = User.query.get(int(user_id))
    if not u:
        return None
    return AuthUser(u)

def generate_admin_token(user_id, ttl=30):
    token = secrets.token_urlsafe(24)
    key = f"admin_token:{token}"
    redis_client.setex(key, ttl, str(user_id))
    return token

def validate_admin_token(token):
    key = f"admin_token:{token}"
    val = redis_client.get(key)
    if not val:
        return None
    return int(val)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return render_template('login.html', error='Invalid credentials')
    login_user(AuthUser(user))
    user.last_seen = datetime.datetime.utcnow()
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    username = request.form.get('username')
    password = request.form.get('password')
    if User.query.filter_by(username=username).first():
        return render_template('register.html', error='Username taken')
    u = User(username=username)
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/admin')
@login_required
def admin_console():
    u = User.query.get(int(current_user.id))
    if u.role not in ('admin','moderator','helpdesk'):
        return "Forbidden", 403
    return render_template('admin.html')

@app.route('/admin/audit')
@login_required
def admin_audit():
    u = User.query.get(int(current_user.id))
    if u.role != 'admin':
        return "Forbidden", 403
    return render_template('audit.html')

@app.route('/api/admin_token', methods=['GET'])
@login_required
def api_admin_token():
    u = User.query.get(int(current_user.id))
    if u.role not in ('admin','moderator','helpdesk'):
        return jsonify({'error':'forbidden'}), 403
    token = generate_admin_token(u.id, ttl=30)
    return jsonify({'token': token, 'ttl': 30})

@app.route('/api/players', methods=['GET'])
@login_required
def api_players():
    rows = User.query.all()
    out = []
    for r in rows:
        out.append({
            'id': r.id,
            'username': r.username,
            'role': r.role,
            'cash': r.cash,
            'rep': r.rep,
            'rank_index': r.rank_index,
            'last_seen': r.last_seen.isoformat() if r.last_seen else None
        })
    return jsonify(out)

@app.route('/api/modify', methods=['POST'])
@login_required
def api_modify():
    actor = User.query.get(int(current_user.id))
    if actor.role not in ('moderator','admin'):
        return jsonify({'error':'forbidden'}), 403
    data = request.json or {}
    uid = int(data.get('user_id') or 0)
    user = User.query.get(uid)
    if not user:
        return jsonify({'error':'no_user'}), 404
    changed = {}
    if 'cash' in data:
        old = user.cash; user.cash = float(data['cash']); changed['cash'] = {'old': old, 'new': user.cash}
    if 'rep' in data:
        old = user.rep; user.rep = int(data['rep']); changed['rep'] = {'old': old, 'new': user.rep}
    if 'rank_index' in data:
        old = user.rank_index; user.rank_index = int(data['rank_index']); changed['rank_index'] = {'old': old, 'new': user.rank_index}
    if 'role' in data and actor.role == 'admin':
        old = user.role; user.role = data['role']; changed['role'] = {'old': old, 'new': user.role}
    db.session.add(AuditLog(actor_id=actor.id, target_id=user.id, action='modify', details=str(changed)))
    db.session.commit()
    payload = {
        'user_id': user.id, 'username': user.username,
        'cash': user.cash, 'rep': user.rep, 'rank_index': user.rank_index, 'role': user.role,
        'ts': datetime.datetime.utcnow().isoformat()
    }
    socketio.emit('admin_update', payload, room='admin_room')
    return jsonify({'ok': True})

@app.route('/api/action', methods=['POST'])
@login_required
def api_action():
    data = request.json or {}
    action = data.get('action')
    user = User.query.get(int(current_user.id))
    if action == 'crime':
        base = 20 + user.rep * 0.05 + user.rank_index * 10
        earn = int(base)
        user.cash += earn
        user.rep += int(earn/10)
        user.last_seen = datetime.datetime.utcnow()
        db.session.add(AuditLog(actor_id=user.id, target_id=user.id, action='crime', details=str({'earn': earn})))
        db.session.commit()
    payload = {
        'user_id': user.id, 'username': user.username,
        'cash': user.cash, 'rep': user.rep, 'rank_index': user.rank_index, 'role': user.role,
        'ts': datetime.datetime.utcnow().isoformat()
    }
    socketio.emit('admin_update', payload, room='admin_room')
    return jsonify({'ok': True, 'cash': user.cash, 'rep': user.rep})

@app.route('/api/notes', methods=['POST'])
@login_required
def api_notes():
    data = request.json or {}
    target = int(data.get('user_id') or 0)
    text = data.get('text','')
    n = Note(user_id=target, author_id=int(current_user.id), text=text)
    db.session.add(n)
    db.session.commit()
    return jsonify({'ok': True})

@app.route('/api/audit', methods=['GET'])
@login_required
def api_audit():
    u = User.query.get(int(current_user.id))
    if u.role != 'admin':
        return jsonify({'error':'forbidden'}), 403
    limit = int(request.args.get('limit', 200))
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    out = []
    for l in logs:
        out.append({'id': l.id, 'actor_id': l.actor_id, 'target_id': l.target_id, 'action': l.action, 'details': l.details, 'created_at': l.created_at.isoformat()})
    return jsonify(out)

@socketio.on('connect')
def on_connect():
    pass

@socketio.on('admin_auth')
def on_admin_auth(data):
    token = data.get('token')
    uid = validate_admin_token(token)
    if not uid:
        emit('admin_auth_result', {'ok': False, 'reason': 'invalid_token'})
        return
    u = User.query.get(uid)
    if not u or u.role not in ('admin','moderator','helpdesk'):
        emit('admin_auth_result', {'ok': False, 'reason': 'not_staff'})
        return
    join_room('admin_room')
    emit('admin_auth_result', {'ok': True})
    players = User.query.all()
    snap = [{'user_id': p.id, 'username': p.username, 'cash': p.cash, 'rep': p.rep, 'role': p.role, 'rank_index': p.rank_index} for p in players]
    emit('initial_snapshot', snap)

@app.route('/_health')
def health():
    return "OK"

if __name__ == '__main__':
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', role='admin', cash=10000, rep=10000, rank_index=4)
        admin.set_password('adminpass')
        mod = User(username='mod', role='moderator', cash=1000, rep=1000); mod.set_password('modpass')
        helpd = User(username='help', role='helpdesk', cash=500, rep=200); helpd.set_password('helppass')
        p1 = User(username='player1', role='player', cash=500, rep=50); p1.set_password('player1')
        p2 = User(username='player2', role='player', cash=1200, rep=200); p2.set_password('player2')
        db.session.add_all([admin, mod, helpd, p1, p2])
        db.session.commit()
        print('Created sample users: admin/mod/help/player1/player2 (passwords adminpass/modpass/helppass/player1/player2)')
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
