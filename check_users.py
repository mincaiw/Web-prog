import sqlite3
import os

users_db_path = os.path.abspath('users.db')

conn = sqlite3.connect(users_db_path)
cursor = conn.cursor()

cursor.execute("SELECT * FROM users")
rows = cursor.fetchall()

for row in rows:
    print(row)

conn.close()
