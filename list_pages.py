# list_pages.py
import os
import sqlite3
import json

# Adjust this path if your DB is elsewhere
DATABASE = os.path.join("backend", "site.db")

def list_pages():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, slug, published FROM pages")
    rows = cursor.fetchall()
    if not rows:
        print("No pages found in the database.")
        return
    print("Pages in DB:")
    for row in rows:
        print(f"ID: {row['id']}, Title: {row['title']}, Slug: {row['slug']}, Published: {row['published']}")

if __name__ == "__main__":
    list_pages()
