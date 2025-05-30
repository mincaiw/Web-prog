import sqlite3

def get_found_items():
    conn = sqlite3.connect('instance/yonsei.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, prdt_cl_nm, start_ymd, prdt_nm, ubuilding, image_path
        FROM found_items
        ORDER BY start_ymd DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return rows

