# show_pages.py
from backend.database import create_connection, get_all_pages_db

def main():
    conn = create_connection()
    pages = get_all_pages_db(conn)
    if pages:
        print("Imported Pages:")
        for page in pages:
            print(f"- {page['title']} (slug: {page['slug']})")
    else:
        print("No pages found in the database.")
    conn.close()

if __name__ == "__main__":
    main()
