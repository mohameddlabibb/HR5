# auto_init_db_json.py
import json
from werkzeug.security import generate_password_hash
from database import create_connection, create_table, create_user

def add_column_if_not_exists(conn, table_name, column_name, column_type):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name});")
    existing_columns = [col[1] for col in cursor.fetchall()]
    if column_name not in existing_columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type};")
        print(f"Added column '{column_name}' to '{table_name}'.")

def initialize_database_from_json(schema_file="schema.json"):
    # Load schema from JSON
    with open(schema_file, "r") as f:
        schema = json.load(f)

    conn = create_connection()

    for table, data in schema.items():
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
    print("Database fully initialized and updated from JSON.")

if __name__ == "__main__":
    initialize_database_from_json()
