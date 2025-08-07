import sqlite3

# Connect to database (it will create data.db if it doesn't exist)
conn = sqlite3.connect('data.db')
cursor = conn.cursor()

# Create uploads table if it doesn't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS uploads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    upload_time TEXT NOT NULL
)
''')

# Commit and close connection
conn.commit()
conn.close()

print("✅ Table 'uploads' created successfully.")
