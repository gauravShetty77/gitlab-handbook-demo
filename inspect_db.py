import sqlite3

conn = sqlite3.connect("vectorstore/chroma.sqlite3")

# Check migrations schema
cursor = conn.execute("PRAGMA table_info(migrations)")
print("Migrations columns:", [r[1] for r in cursor.fetchall()])

# Get latest migration
rows = conn.execute("SELECT * FROM migrations ORDER BY rowid DESC LIMIT 5").fetchall()
print("Latest migrations:", rows)

# Check collections
rows = conn.execute("SELECT id, name, dimension FROM collections LIMIT 5").fetchall()
print("Collections:", rows)

# Count embeddings
count = conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
print(f"Total embeddings: {count}")

conn.close()
