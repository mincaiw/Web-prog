import sqlite3
import os

yonsei_db_path = os.path.abspath(os.path.join('instance', 'yonsei.db'))

conn = sqlite3.connect(yonsei_db_path)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS found_items_new (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prdt_cl_nm TEXT,
        start_ymd TEXT,
        prdt_nm TEXT,
        ubuilding TEXT,
        image_path TEXT
    )
''')

cursor.execute('''
    INSERT INTO found_items_new (id, prdt_cl_nm, start_ymd, prdt_nm, ubuilding, image_path)
    SELECT id, prdt_cl_nm, start_ymd, prdt_nm, ubuilding, image_path
    FROM found_items
''')

cursor.execute('DROP TABLE found_items')

cursor.execute('ALTER TABLE found_items_new RENAME TO found_items')

conn.commit()
conn.close()