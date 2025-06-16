import sys, os, sqlite3
from functools import wraps
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "vendor"))

from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from flask_cors import CORS
from auth import auth_bp

from dotenv import load_dotenv

load_dotenv()

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

def get_found_items_from_db():
    conn = sqlite3.connect('instance/yonsei.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, prdt_cl_nm, start_ymd, prdt_nm, ubuilding, image_path
        FROM found_items
        ORDER BY start_ymd DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.getenv("SECRET_KEY", "yonsei_uni_140_default_secret")
CORS(app)

app.register_blueprint(auth_bp, url_prefix='/auth')

# Set language based on URL path before each request
@app.before_request
def set_language_for_g():
    g.lang = 'ko'
    if request.path.startswith('/en/'):
        g.lang = 'en'
    elif request.path.startswith('/auth/ko/'):
        g.lang = 'ko'
    elif request.path.startswith('/auth/en/'):
        g.lang = 'en'
    session['lang'] = g.lang

def get_current_user_email():
    return session.get('email')

@app.route('/')
def home():
    return redirect(url_for('index', lang_code='ko'))

@app.route('/<string:lang_code>/')
def index(lang_code):
    user_email = get_current_user_email()
    return render_template('base.html', user_email=user_email, lang=lang_code, title="Home")

@app.route('/<string:lang_code>/find')
def find(lang_code):
    user_email = get_current_user_email()
    items = get_found_items_from_db()

    building_map_ko = {
        "101": "언더우드기념도서관",
        "203": "운동장",
        "305": "송도1학사",
        "405": "송도2학사",
        "302": "자유관A",
        "301": "자유관B",
        "510": "저에너지친환경실험주택",
        "501": "종합관",
        "401": "진리관A",
        "402": "진리관B",
        "502": "진리관C",
        "503": "진리관D"
    }

    building_map_en = {
        "101": "Underwood Memorial Library",
        "203": "Soccer Field",
        "305": "Songdo Dorm A, B, C",
        "405": "Songdo Dorm D, E, F, G",
        "302": "Libertas Hall A",
        "301": "Libertas Hall B",
        "510": "Pilot Project of Sustainable Housing",
        "501": "Vision Hall",
        "401": "Veritas Hall A",
        "402": "Veritas Hall B",
        "502": "Veritas Hall C",
        "503": "Veritas Hall D"
    }
    

    building_map = building_map_ko if lang_code == 'ko' else building_map_en
    
    for item in items:
        item['ubuilding'] = building_map.get(item['ubuilding'], item['ubuilding'])
        if item['image_path']:
            item['image_path'] = item['image_path'].replace("static/", "").replace("\\", "/")
        else:
            item['image_path'] = 'images/placeholder.png'
            
    if lang_code == 'ko':
        return render_template('ko/find_ko.html', user_email=user_email, items=items, lang=lang_code, title="습득물 검색")
    else:
        return render_template('en/find_en.html', user_email=user_email, items=items, lang=lang_code, title="Search Found Items")

@app.route('/<string:lang_code>/register')
def register(lang_code):
    return redirect(url_for(f'auth_bp.register_{lang_code}'))

@app.route('/<string:lang_code>/map')
def map(lang_code):
    naver_client_id = os.getenv("NAVER_CLIENT_ID")
    if lang_code == 'ko':
        return render_template('ko/map_ko.html', lang=lang_code, title="연세대학교 국제캠퍼스 지도", naver_client_id=naver_client_id)
    else:
        return render_template('en/map_en.html', lang=lang_code, title="Yonsei University International Campus Map", naver_client_id=naver_client_id)

# Initialize user database
def init_db():
    conn = None
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                reset_token TEXT,
                token_expiration TEXT
            )
        ''')
        conn.commit()
        print("Database 'users.db' initialized/checked successfully.")
    except sqlite3.Error as e:
        print(f"Error initializing database: {e}")
    finally:
        if conn:
            conn.close()

# Initialize found_items database
def init_yonsei_db():
    conn = None
    try:
        conn = sqlite3.connect('instance/yonsei.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS found_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prdt_cl_nm TEXT,
                start_ymd TEXT,
                prdt_nm TEXT,
                ubuilding TEXT,
                image_path TEXT,
                user_id TEXT
            )
        ''')
        conn.commit()
        print("Database 'instance/yonsei.db' initialized/checked successfully.")
    except sqlite3.Error as e:
        print(f"Error initializing yonsei.db: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    init_db()
    init_yonsei_db()
    app.run(debug=True)
