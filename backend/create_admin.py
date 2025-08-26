import os
import sys
sys.path.append('.')
from backend.database import create_connection
from werkzeug.security import generate_password_hash
from config import ADMIN_USERNAME, ADMIN_PASSWORD_HASH

conn = create_connection()
cursor = conn.cursor()
cursor.execute("SELECT * FROM users WHERE username = ?", (ADMIN_USERNAME,))
user = cursor.fetchone()

if not user:
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (ADMIN_USERNAME, ADMIN_PASSWORD_HASH))
    conn.commit()
    print('Admin user created')
else:
    print('Admin user already exists')

conn.close()
