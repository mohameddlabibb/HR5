# backend/init_db.py

import sqlite3
from werkzeug.security import generate_password_hash

DB_PATH = "instance/database.db"   # adjust if your DB file is stored elsewhere

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            token TEXT
        )
    """)

    # Insert a test admin user
    try:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            ("test", generate_password_hash("123"))
        )
        print("✅ Test user 'test' created with password '123'")
    except sqlite3.IntegrityError:
        print("ℹ️ Test user already exists, skipping insert.")

    conn.commit()
    conn.close()
    print("✅ Database initialized.")

if __name__ == "__main__":
    init_db()
