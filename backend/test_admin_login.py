import unittest
import json
from backend.app import app, get_db
from backend.config import ADMIN_USERNAME, ADMIN_PASSWORD_HASH
import sqlite3
from werkzeug.security import generate_password_hash

class AdminLoginTestCase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        self.db = get_db()
        self.db.execute("DROP TABLE IF EXISTS users")
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                token TEXT
            )
        """)
        self.db.commit()
        # Create a test admin user
        hashed_password = generate_password_hash("adminpass")
        self.db.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("admin", hashed_password))
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.app_context.pop()

    def test_admin_login_success(self):
        response = self.app.post('/api/admin/login', json={
            'username': 'admin',
            'password': 'adminpass'
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertIn('access_token', data)

    def test_admin_login_failure(self):
        response = self.app.post('/api/admin/login', json={
            'username': 'admin',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data['message'], 'Invalid credentials')

if __name__ == '__main__':
    unittest.main()
