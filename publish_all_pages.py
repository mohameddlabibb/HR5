# publish_all_pages.py
import os
import sqlite3

# Path to your database
DATABASE = os.path.join("backend", "site.db")

def publish_all_pages():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("UPDATE pages SET published = 1")
    conn.commit()
    print(f"{cursor.rowcount} pages marked as published.")
    conn.close()

if __name__ == "__main__":
    publish_all_pages()
