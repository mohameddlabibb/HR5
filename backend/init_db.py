# init_db.py
import sqlite3
from sqlite3 import Error
from werkzeug.security import generate_password_hash
from database import create_connection, create_table, create_user

def add_column_if_not_exists(conn, table_name, column_name, column_type):
    cursor = conn.cursor()
    # Check if column already exists
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = [col[1] for col in cursor.fetchall()]
    if column_name not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type};")
        print(f"Added column '{column_name}' to table '{table_name}'")

def initialize_database():
    conn = create_connection()

    # --- Table definitions ---
    tables = {
        "users": """
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          username TEXT NOT NULL UNIQUE,
          password TEXT NOT NULL,
          token TEXT UNIQUE
        );
        """,
        "menus": """
        CREATE TABLE IF NOT EXISTS menus (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL UNIQUE,
          menu_data TEXT NOT NULL
        );
        """,
        "widgets": """
        CREATE TABLE IF NOT EXISTS widgets (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL UNIQUE,
          widget_type TEXT NOT NULL,
          widget_data TEXT NOT NULL
        );
        """,
        "pages": """
        CREATE TABLE IF NOT EXISTS pages (
          id TEXT PRIMARY KEY,
          title TEXT NOT NULL,
          slug TEXT UNIQUE,
          content TEXT,
          published BOOLEAN NOT NULL,
          is_chapter BOOLEAN NOT NULL,
          parent_id TEXT,
          design TEXT,
          meta_description TEXT,
          meta_keywords TEXT,
          custom_css TEXT,
          FOREIGN KEY (parent_id) REFERENCES pages (id) ON DELETE CASCADE
        );
        """,
        "settings": """
        CREATE TABLE IF NOT EXISTS settings (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          setting_key TEXT NOT NULL UNIQUE,
          setting_value TEXT
        );
        """
    }

    # --- Create tables safely ---
    for name, sql in tables.items():
        create_table(conn, sql)
        print(f"Table '{name}' ensured.")

    # --- Example: Add new columns safely ---
    add_column_if_not_exists(conn, "users", "last_login", "TEXT")  # new optional column
    add_column_if_not_exists(conn, "pages", "summary", "TEXT")      # another optional column

    # --- Create admin user safely ---
    hashed_password = generate_password_hash("password")
    create_user(conn, ("admin", hashed_password))

    conn.close()
    print("Database initialized and updated safely.")

if __name__ == "__main__":
    initialize_database()
