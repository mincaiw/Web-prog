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
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

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
app.secret_key = 'yonsei_uni_140' # It's better to put this in .env as well
CORS(app)

app.register_blueprint(auth_bp, url_prefix='/auth')

# Before each request, determine the language based on the URL path
@app.before_request
def set_language_for_g():
    # Default language is Korean
    g.lang = 'ko'
    # Check if the URL path starts with '/en'
    if request.path.startswith('/en/'): # Use /en/ to distinguish from /en route directly
        g.lang = 'en'
    # For the root path '/', redirect to the default language's index
    if request.path == '/':
        g.lang = 'ko' # Default for root route

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
    return render_template('base.html', user_email=user_email, lang=lang_code)

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
        item['ubuilding'] = building_map.get(item['ubuilding'], item['ubuilding'])
        item['image_path'] = item['image_path'].replace("static/", "").replace("\\", "/")

    return render_template('base.html', user_email=user_email, items=items, lang=lang_code)

@app.route('/<string:lang_code>/register')
def register(lang_code):
    user_email = get_current_user_email()
    return render_template('base.html', user_email=user_email, lang=lang_code)

@app.route('/<string:lang_code>/map')
def map(lang_code):
    return render_template('base.html', lang=lang_code)

@app.route('/<string:lang_code>/login', methods=['GET','POST'])
def login(lang_code):
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        if user and user[3] == password: # Assuming user[3] is the password
            session['email'] = email # Store email in session for easy retrieval
            # Redirect to the register page in the current language after successful login
            return redirect(url_for('register', lang_code=lang_code))
        else:
            if lang_code == 'ko':
                flash('로그인 실패: 이메일 또는 비밀번호가 올바르지 않습니다.')
            else: # English
                flash('Login Failed: Incorrect Email or Password')
            # Assuming your login form is part of base.html or a separate template block
            return render_template('base.html', lang=lang_code, show_login_form=True) # You might need a flag to show the form
    # For GET request, render the login page
    return render_template('base.html', lang=lang_code) # This assumes base.html can render the login form via a block or includes.

@app.route('/<string:lang_code>/signup')
def signup(lang_code):
    # This route will also use base.html, assuming signup form is rendered via a block
    return render_template('base.html', lang=lang_code)

@app.route('/<string:lang_code>/logout')
def logout(lang_code):
    session.pop('email', None)
    # Redirect to the index page in the current language after logout
    return redirect(url_for('index', lang_code=lang_code))


if __name__ == '__main__':
    app.run(debug=True)