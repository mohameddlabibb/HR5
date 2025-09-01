import sys
import os
import uuid
from datetime import datetime
import json
import sqlite3
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from database import create_connection, add_page_db

def import_pages_from_json(json_file="data/pages.json"):
    conn = create_connection()
    cursor = conn.cursor()

    with open(json_file, "r") as f:
        pages_data = json.load(f)

    def insert_page(page, parent_id=None):
        page_id = page['id']
        title = page['title']
        slug = page['slug']
        content = page['content']
        published = page['published']
        design = page['design']
        is_chapter = bool(page.get('children'))
        
        add_page_db(conn, page_id, title, slug, content, published, is_chapter, parent_id, design, None, None, None, None, None)

        if 'children' in page and page['children']:
            for child in page['children']:
                insert_page(child, page_id)
        conn.commit()

    for page in pages_data:
        insert_page(page)

    conn.commit()
    conn.close()
    print("Pages imported successfully from JSON.")

if __name__ == "__main__":
    import_pages_from_json()
