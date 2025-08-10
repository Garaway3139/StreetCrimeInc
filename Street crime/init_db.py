# Run this to initialize DB and create sample users
from app import db, User
db.create_all()
if not User.query.filter_by(username='admin').first():
    admin = User(username='admin', role='admin', cash=10000, rep=10000, rank_index=4)
    admin.set_password('adminpass')
    mod = User(username='mod', role='moderator', cash=1000, rep=1000)
    mod.set_password('modpass')
    helpd = User(username='help', role='helpdesk', cash=500, rep=200)
    helpd.set_password('helppass')
    p1 = User(username='player1', role='player', cash=500, rep=50)
    p1.set_password('player1')
    p2 = User(username='player2', role='player', cash=1200, rep=200)
    p2.set_password('player2')
    db.session.add_all([admin, mod, helpd, p1, p2])
    db.session.commit()
    print('Created sample users.')
else:
    print('Users already exist.') 
