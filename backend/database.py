import sqlite3
from sqlite3 import Error

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

from werkzeug.security import generate_password_hash # Import for password hashing

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

    if conn is not None:
        create_table(conn, create_users_table)
        print("Users table created successfully")
        create_table(conn, create_menus_table)
        print("Menus table created successfully")
        create_table(conn, create_widgets_table)
        print("Widgets table created successfully")

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
