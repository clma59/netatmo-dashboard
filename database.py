import sqlite3

conn = sqlite3.connect("weather.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS temperatures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    temperature REAL,
    humidity REAL
)
""")

conn.commit()
conn.close()

print("Base créée")