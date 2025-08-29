import sys
import os
import json
from backend.database import create_connection, add_page_db

PAGES_FOLDER = os.path.join(os.path.dirname(__file__), "pages")
conn = create_connection()

# Keep track of folder path → parent_id
folder_parent_map = {}

def insert_page(page, parent_id=None):
    """Insert a single page into the database with optional parent_id."""
    add_page_db(
        conn,
        page.get("id"),
        page.get("title"),
        page.get("slug"),
        page.get("content"),
        page.get("published", True),
        page.get("is_chapter", False),
        parent_id,
        page.get("design", {}),
        page.get("meta_description"),
        page.get("meta_keywords"),
        page.get("custom_css")
    )

def import_pages_from_folder(folder, parent_id=None):
    """Recursively import JSON pages, setting parent_id based on folder structure."""
    for root, _, files in os.walk(folder):
        # Sort files to ensure consistent order
        files.sort()
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                print(f"Importing {file_path}...")
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for page in data:
                            insert_page(page, parent_id)
                            # If this page is a chapter, we can use its id as new parent for nested pages
                            if page.get("is_chapter"):
                                folder_parent_map[root] = page.get("id")
                    elif isinstance(data, dict):
                        insert_page(data, parent_id)
                        if data.get("is_chapter"):
                            folder_parent_map[root] = data.get("id")
                    else:
                        print(f"Skipped {file_path}: unknown JSON format")

        # Recursively handle subfolders
        for subfolder in next(os.walk(folder))[1]:
            subfolder_path = os.path.join(root, subfolder)
            # Determine parent_id for this subfolder
            sub_parent_id = folder_parent_map.get(root, parent_id)
            import_pages_from_folder(subfolder_path, parent_id=sub_parent_id)

if __name__ == "__main__":
    import_pages_from_folder(PAGES_FOLDER)
    print("All pages imported successfully with hierarchy!")
    conn.close()
