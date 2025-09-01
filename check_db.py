import sqlite3

db = r"E:\HR5\site.db"
print("DB:", db)

conn = sqlite3.connect(db)
c = conn.cursor()

# List all tables
tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")]
print("tables =", tables)

if "pages" in tables:
    count = c.execute("SELECT COUNT(*) FROM pages").fetchone()[0]
    print("pages_count =", count)

    rows = c.execute("SELECT id, title, slug FROM pages LIMIT 5").fetchall()
    print("sample =", rows)
else:
    print("⚠️ No 'pages' table found")

conn.close()
