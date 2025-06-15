import sys, os, sqlite3
from functools import wraps
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "vendor"))

from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from flask_cors import CORS
from auth import auth_bp # Assuming auth.py contains auth_bp

from dotenv import load_dotenv

load_dotenv()
# Corrected variable names for os.getenv calls
# Ensure these environment variables are set in your .env file
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET") # Ensure this is also set if needed elsewhere

def get_found_items():
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

app = Flask(__name__, static_folder='static', template_folder='templates') # Explicitly set template_folder
app.secret_key = os.getenv("SECRET_KEY", "yonsei_uni_140_default_secret") # Use environment variable for secret key, provide default
CORS(app)

app.register_blueprint(auth_bp, url_prefix='/auth') # All auth routes are now under /auth

# Before each request, determine the language based on the URL path
@app.before_request
def set_language_for_g():
    # Default language is Korean
    g.lang = 'ko'
    # Check if the URL path starts with '/en'
    if request.path.startswith('/en/'):
        g.lang = 'en'
    # For the root path '/', redirect to the default language's index
    # IMPORTANT: Ensure this logic correctly sets g.lang for ALL routes, including blueprint routes
    elif request.path.startswith('/auth/ko/'):
        g.lang = 'ko'
    elif request.path.startswith('/auth/en/'):
        g.lang = 'en'
    # If it's the root path, always set to 'ko' and redirect (handled by home())
    # Otherwise, g.lang will remain 'ko' by default if no '/en/' is found, which is fine.


# Helper to get user email consistently from session
def get_current_user_email():
    return session.get('email')

# Consolidated index route: handles both / and /<lang_code>/
@app.route('/')
def home():
    # Redirect to the default Korean index page
    return redirect(url_for('index', lang_code='ko'))

@app.route('/<string:lang_code>/')
def index(lang_code):
    user_email = get_current_user_email()
    # Pass the determined language to the base template
    return render_template('base.html', user_email=user_email, lang=lang_code, title="Home")

@app.route('/<string:lang_code>/find')
def find(lang_code):
    user_email = get_current_user_email()
    items = get_found_items()

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

    building_map_en = { # Example English translations for building names
        "101": "Underwood Memorial Library",
        "203": "Sports Field",
        "305": "Songdo Dorm 1",
        "405": "Songdo Dorm 2",
        "302": "Jayugwan A",
        "301": "Jayugwan B",
        "510": "Low-Energy Eco-Friendly Research Building",
        "501": "General Building",
        "401": "Jingrigwan A",
        "402": "Jingrigwan B",
        "502": "Jingrigwan C",
        "503": "Jingrigwan D"
    }

    # Select the appropriate map based on language
    building_map = building_map_ko if lang_code == 'ko' else building_map_en
    
    for item in items:
        # Use .get() with a fallback to avoid KeyError if ubuilding code is not in map
        item['ubuilding'] = building_map.get(item['ubuilding'], item['ubuilding'])
        # Ensure image paths are correctly formatted for web access
        if item['image_path']:
            item['image_path'] = item['image_path'].replace("static/", "").replace("\\", "/")

    return render_template('base.html', user_email=user_email, items=items, lang=lang_code, title="Find Items")

# This route is for registering items (not user signup)
@app.route('/<string:lang_code>/register')
def register(lang_code):
    user_email = get_current_user_email()
    return render_template('base.html', user_email=user_email, lang=lang_code, title="Register")

# MODIFIED: Map route to pass Naver Client ID and render specific map template
@app.route('/<string:lang_code>/map')
def map(lang_code):
    naver_client_id = os.getenv("NAVER_CLIENT_ID") # Get the client ID from environment
    if lang_code == 'ko':
        return render_template('ko/map_ko.html', lang=lang_code, title="연세대학교 국제캠퍼스 지도", naver_client_id=naver_client_id)
    else: # English
        return render_template('en/map_en.html', lang=lang_code, title="Yonsei University International Campus Map", naver_client_id=naver_client_id)

# REMOVED: Redundant login route (now handled by auth_bp)
# @app.route('/<string:lang_code>/login', methods=['GET','POST'])
# def login(lang_code):
#     ... (removed content) ...

# REMOVED: Redundant signup route (now handled by auth_bp)
# @app.route('/<string:lang_code>/signup', methods=['GET', 'POST'])
# def signup(lang_code):
#     ... (removed content) ...

# REMOVED: Redundant logout route (now handled by auth_bp)
# @app.route('/<string:lang_code>/logout')
# def app_logout(lang_code): # Renamed to app_logout to avoid conflict if both were active
#     session.pop('email', None)
#     return redirect(url_for('index', lang_code=lang_code))


# Helper to initialize the user database if it doesn't exist
def init_db():
    conn = None
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        # IMPORTANT: Ensure user_id and email are UNIQUE to prevent duplicates
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

if __name__ == '__main__':
    init_db() # Initialize the users database when the app starts
    app.run(debug=True)
