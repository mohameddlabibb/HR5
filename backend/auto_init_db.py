# auto_init_db.py
import sqlite3
from sqlite3 import Error
from werkzeug.security import generate_password_hash
from database import create_connection, create_table, create_user

# Define your desired database schema
SCHEMA = {
    "users": {
        "columns": {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "username": "TEXT NOT NULL UNIQUE",
            "password": "TEXT NOT NULL",
            "token": "TEXT UNIQUE",
            "last_login": "TEXT"  # optional new column
        }
    },
    "menus": {
        "columns": {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "name": "TEXT NOT NULL UNIQUE",
            "menu_data": "TEXT NOT NULL"
        }
    },
    "widgets": {
        "columns": {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "name": "TEXT NOT NULL UNIQUE",
            "widget_type": "TEXT NOT NULL",
            "widget_data": "TEXT NOT NULL"
        }
    },
    "pages": {
        "columns": {
            "id": "TEXT PRIMARY KEY",
            "title": "TEXT NOT NULL",
            "slug": "TEXT UNIQUE",
            "content": "TEXT",
            "published": "BOOLEAN NOT NULL",
            "is_chapter": "BOOLEAN NOT NULL",
            "parent_id": "TEXT",
            "design": "TEXT",
            "meta_description": "TEXT",
            "meta_keywords": "TEXT",
            "custom_css": "TEXT",
            "summary": "TEXT"  # optional new column
        }
    },
    "settings": {
        "columns": {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "setting_key": "TEXT NOT NULL UNIQUE",
            "setting_value": "TEXT"
        }
    }
}

def add_column_if_not_exists(conn, table_name, column_name, column_type):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name});")
    existing_columns = [col[1] for col in cursor.fetchall()]
    if column_name not in existing_columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type};")
        print(f"Added column '{column_name}' to '{table_name}'.")

def initialize_database():
    conn = create_connection()
    for table, data in SCHEMA.items():
        # Build CREATE TABLE statement
        columns_sql = ", ".join([f"{col} {typ}" for col, typ in data["columns"].items()])
        create_table_sql = f"CREATE TABLE IF NOT EXISTS {table} ({columns_sql});"
        create_table(conn, create_table_sql)
        print(f"Ensured table '{table}' exists.")

        # Add missing columns
        for col, typ in data["columns"].items():
            add_column_if_not_exists(conn, table, col, typ)

    # Ensure admin user exists
    hashed_password = generate_password_hash("password")
    create_user(conn, ("admin", hashed_password))

    conn.close()
    print("Database fully initialized and updated automatically.")

if __name__ == "__main__":
    initialize_database()
