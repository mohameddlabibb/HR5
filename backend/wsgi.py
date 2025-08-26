import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from .app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password=generate_password_hash('password'))
        db.session.add(admin)
        db.session.commit()
        print('Admin user created')
    else:
        print('Admin user already exists')

if __name__ == "__main__":
    app.run(debug=True)
