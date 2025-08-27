import sqlite3
from sqlite3 import Error
from werkzeug.security import generate_password_hash # Import for password hashing
import json # Import json for serializing page_data

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect('site.db')
        print("Connection to SQLite DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")
    return conn

def create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(f"The error '{e}' occurred")

def create_user(conn, user_data):
    sql = ''' INSERT OR IGNORE INTO users(username, password)
              VALUES(?,?) '''
    cur = conn.cursor()
    cur.execute(sql, user_data)
    conn.commit()
    return cur.lastrowid

def get_user(conn, username):
    sql = ''' SELECT * FROM users WHERE username = ? '''
    cur = conn.cursor()
    cur.execute(sql, (username,))
    return cur.fetchone()

# --- Database Helper Functions for Pages ---

def add_page_db(conn, page_id, title, slug, content, published, is_chapter, parent_id, design, meta_description, meta_keywords, custom_css):
    """Inserts a new page or chapter into the database."""
    sql = ''' INSERT INTO pages(id, title, slug, content, published, is_chapter, parent_id, design, meta_description, meta_keywords, custom_css)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, (page_id, title, slug, content, published, is_chapter, parent_id, json.dumps(design), meta_description, meta_keywords, custom_css))
    conn.commit()
    return cur.lastrowid

def get_all_pages_db(conn):
    """Retrieves all pages/chapters from the database."""
    sql = ''' SELECT * FROM pages '''
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    pages = []
    for row in rows:
        page = dict(row)
        page['published'] = bool(page['published']) # Convert integer to boolean
        page['is_chapter'] = bool(page['is_chapter']) # Convert integer to boolean
        page['design'] = json.loads(page['design']) if page['design'] else {}
        pages.append(page)
    return pages

def get_page_by_id_db(conn, page_id):
    """Retrieves a single page/chapter by its ID."""
    sql = ''' SELECT * FROM pages WHERE id = ? '''
    cur = conn.cursor()
    cur.execute(sql, (page_id,))
    row = cur.fetchone()
    if row:
        page = dict(row)
        page['published'] = bool(page['published'])
        page['is_chapter'] = bool(page['is_chapter'])
        page['design'] = json.loads(page['design']) if page['design'] else {}
        return page
    return None

def get_page_by_slug_db(conn, slug):
    """Retrieves a single page by its slug."""
    sql = ''' SELECT * FROM pages WHERE slug = ? '''
    cur = conn.cursor()
    cur.execute(sql, (slug,))
    row = cur.fetchone()
    if row:
        page = dict(row)
        page['published'] = bool(page['published'])
        page['is_chapter'] = bool(page['is_chapter'])
        page['design'] = json.loads(page['design']) if page['design'] else {}
        return page
    return None

def update_page_db(conn, page_id, title, slug, content, published, is_chapter, parent_id, design, meta_description, meta_keywords, custom_css):
    """Updates an existing page or chapter in the database."""
    sql = ''' UPDATE pages
              SET title = ?,
                  slug = ?,
                  content = ?,
                  published = ?,
                  is_chapter = ?,
                  parent_id = ?,
                  design = ?,
                  meta_description = ?,
                  meta_keywords = ?,
                  custom_css = ?
              WHERE id = ? '''
    cur = conn.cursor()
    cur.execute(sql, (title, slug, content, published, is_chapter, parent_id, json.dumps(design), meta_description, meta_keywords, custom_css, page_id))
    conn.commit()
    return cur.rowcount

def delete_page_db(conn, page_id):
    """Deletes a page or chapter by its ID."""
    sql = ''' DELETE FROM pages WHERE id = ? '''
    cur = conn.cursor()
    cur.execute(sql, (page_id,))
    conn.commit()
    return cur.rowcount

if __name__ == '__main__':
    conn = create_connection()

    create_users_table = """
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT NOT NULL UNIQUE,
      password TEXT NOT NULL
    );
    """

    create_menus_table = """
    CREATE TABLE IF NOT EXISTS menus (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL UNIQUE,
      menu_data TEXT NOT NULL
    );
    """

    create_widgets_table = """
    CREATE TABLE IF NOT EXISTS widgets (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL UNIQUE,
      widget_type TEXT NOT NULL,
      widget_data TEXT NOT NULL
    );
    """

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

    if conn is not None:
        create_table(conn, create_users_table)
        print("Users table created successfully")
        create_table(conn, create_menus_table)
        print("Menus table created successfully")
        create_table(conn, create_widgets_table)
        print("Widgets table created successfully")
        create_table(conn, create_pages_table)
        print("Pages table created successfully")

        create_settings_table = """
        CREATE TABLE IF NOT EXISTS settings (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          setting_key TEXT NOT NULL UNIQUE,
          setting_value TEXT
        );
        """
        create_table(conn, create_settings_table)
        print("Settings table created successfully")

        # Example usage:
        # Create an admin user (replace with a secure password hashing method in production)
        # Hash the password before storing it
        hashed_password = generate_password_hash("password")
        user_data = ("admin", hashed_password)
        user_id = create_user(conn, user_data)
        if user_id: # Only print if a new user was actually created
            print(f"Admin user created with id: {user_id}")
        else:
            print("Admin user 'admin' already exists or could not be created.")

        # Retrieve the admin user
        admin_user = get_user(conn, "admin")
        print(f"Admin user details: {admin_user}")

        conn.close()
    else:
        print("Error! cannot create database connection.")
