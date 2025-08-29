import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))
import json
from database import create_connection, add_page_db, get_page_by_id_db

# --- Path setup ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
JSON_FILE = os.path.join(DATA_DIR, "pages.json")

# --- Load JSON data ---
def load_pages_from_json(json_path):
    if not os.path.exists(json_path):
        print(f"JSON file not found: {json_path}")
        return []
    with open(json_path, "r", encoding="utf-8") as f:
        pages = json.load(f)
    return pages

# --- Insert pages into DB ---
def insert_page(conn, page):
    page_id = page.get("id")
    if get_page_by_id_db(conn, page_id):
        print(f"Page '{page.get('title')}' (ID: {page_id}) already exists, skipping.")
        return False
    add_page_db(
        conn,
        page_id,
        page.get("title"),
        page.get("slug"),
        page.get("content"),
        page.get("published", True),
        page.get("is_chapter", False),
        page.get("parent_id"),
        page.get("design", {}),
        page.get("meta_description"),
        page.get("meta_keywords"),
        page.get("custom_css")
    )
    print(f"Page '{page.get('title')}' (ID: {page_id}) imported successfully.")
    return True

# --- Main import function ---
def import_and_publish_pages():
    conn = create_connection()
    if not conn:
        print("Failed to connect to database.")
        return

    pages = load_pages_from_json(JSON_FILE)
    if not pages:
        print("No pages found in JSON file.")
        return

    for page in pages:
        insert_page(conn, page)

    conn.close()
    print("All pages processed.")

# --- Run ---
if __name__ == "__main__":
    import_and_publish_pages()

# Path to your pages folder
PAGES_FOLDER = os.path.join(os.path.dirname(__file__), "pages")

# Connect to DB
conn = create_connection()

def insert_page(page):
    """Insert one page into DB."""
    add_page_db(
        conn,
        page.get("id"),
        page.get("title"),
        page.get("slug"),
        page.get("content"),
        page.get("published", True),
        page.get("is_chapter", False),
        page.get("parent_id"),
        page.get("design", {}),
        page.get("meta_description"),
        page.get("meta_keywords"),
        page.get("custom_css")
    )

def import_pages_from_folder(folder):
    """Recursively import all JSON pages from folder."""
    for root, _, files in os.walk(folder):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                print(f"Importing {file_path}...")
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # If file contains a list of pages
                    if isinstance(data, list):
                        for page in data:
                            insert_page(page)
                    # If file contains a single page object
                    elif isinstance(data, dict):
                        insert_page(data)
                    else:
                        print(f"Skipped {file_path}: unknown JSON format")

if __name__ == "__main__":
    import_pages_from_folder(PAGES_FOLDER)
    print("All pages imported successfully!")
    conn.close()