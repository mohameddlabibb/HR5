import json
import sqlite3
import os
import sys
sys.path.append('.')
from werkzeug.security import generate_password_hash
from database import create_connection, create_table, add_page_db, get_user, create_user

def migrate_pages_from_json_to_db():
    json_file_path = 'data/pages.json'
    conn = create_connection()

    if conn is None:
        print("Error: Could not connect to the database.")
        return

    try:
        # Ensure the pages table exists
        create_pages_table = """
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
        """
        create_table(conn, create_pages_table)
        print("Pages table ensured to exist.")

        if os.path.exists(json_file_path):
            with open(json_file_path, 'r', encoding='utf-8') as f:
                pages_data = json.load(f)

            # Flatten the nested structure for easier insertion
            def flatten_and_assign_parent(items, parent_id=None):
                flat_list = []
                for item in items:
                    page_id = item['id']
                    title = item['title']
                    slug = item.get('slug')
                    content = item.get('content')
                    published = item.get('published', False)
                    is_chapter = item.get('is_chapter', False)
                    design = item.get('design', {})
                    meta_description = item.get('meta_description', '')
                    meta_keywords = item.get('meta_keywords', '')
                    custom_css = item.get('custom_css', '')

                    add_page_db(conn, page_id, title, slug, content, published, is_chapter, parent_id, design, meta_description, meta_keywords, custom_css)
                    print(f"Migrated page: {title} (ID: {page_id})")

                    if 'children' in item and item['children']:
                        flat_list.extend(flatten_and_assign_parent(item['children'], page_id))
                return flat_list

            flatten_and_assign_parent(pages_data)
            print("Migration from pages.json to database completed successfully.")
        else:
            print(f"Warning: {json_file_path} not found. No data to migrate.")

    except Exception as e:
        print(f"An error occurred during migration: {e}")
    finally:
        if conn:
            conn.close()

def setup_initial_admin_user():
    conn = create_connection()
    if conn is None:
        print("Error: Could not connect to the database for admin setup.")
        return

    try:
        create_users_table = """
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          username TEXT NOT NULL UNIQUE,
          password TEXT NOT NULL
        );
        """
        create_table(conn, create_users_table)
        print("Users table ensured to exist for admin setup.")

        # Check if admin user already exists
        admin_user = get_user(conn, "admin")
        if not admin_user:
            hashed_password = generate_password_hash("password") # Default password for initial setup
            user_data = ("admin", hashed_password)
            user_id = create_user(conn, user_data)
            if user_id:
                print(f"Initial admin user 'admin' created with ID: {user_id} and password 'password'. Please change this password immediately!")
            else:
                print("Failed to create initial admin user.")
        else:
            print("Admin user 'admin' already exists. Skipping initial setup.")
    except Exception as e:
        print(f"An error occurred during initial admin user setup: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    print("Starting database migration and initial admin setup...")
    setup_initial_admin_user()
    migrate_pages_from_json_to_db()
    print("Migration and setup process finished.")
