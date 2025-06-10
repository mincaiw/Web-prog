import sys, os, sqlite3
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "vendor"))

from flask import Flask, render_template, request, redirect, url_for, flash  
# from flask_login import login_required, current_user, LoginManager
from flask_cors import CORS
from auth import auth_bp
from dotenv import load_dotenv

load_dotenv()
NAVER_CLIENT_ID=os.getenv("udhwj5en73")
NAVER_CLIENT_SECRET=os.getenv("gL2gWzBkk0bOSN8TnYdpbMRNDFVXPnDP5wdixzgM")
# from werkzeug.utils import secure_filename
from flask import session

def get_found_items():
    conn = sqlite3.connect('instance/yonsei.db')
    conn.row_factory=sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, prdt_cl_nm, start_ymd, prdt_nm, ubuilding, image_path
        FROM found_items
        ORDER BY start_ymd DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows] 


app = Flask(__name__, static_folder='static')
app.secret_key = 'yonsei_uni_140'
CORS(app)

app.register_blueprint(auth_bp, url_prefix='/auth')



@app.route('/')
def home():
    return render_template('ko/index_ko.html')

# English page
@app.route('/en')
def index_en():
    return render_template('en/index_en.html')

@app.route('/en/find')
def find_en():
    return render_template('en/find_en.html')

@app.route('/en/register')
def register_en():
    user_email = session.get('email')
    return render_template('en/register_en.html', user_email=user_email)

@app.route('/en/map')
def map_en():
    return render_template('en/map_en.html')

@app.route('/en/login')
def login_en():
    return render_template('/en/auth/login_en.html')

@app.route('/en/signup')
def signup_en():
    user_email = session.get('email')
    return render_template('en/auth/signup_en.html', user_email=user_email)

# Korean page
@app.route('/ko')
def index_ko():
    user_email = session.get('email')

    if 'user_id' in session:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT email FROM users WHERE id = ?', (session['user_id'],))  # <-- FIXED HERE
        user = cursor.fetchone()
        conn.close()

        if user:
            user_email = user[0]

    return render_template('ko/index_ko.html', user_email=user_email)

@app.route('/ko/find')
def find_ko():
    user_email = session.get('email')  # Lấy email từ session
    items=get_found_items()

    building_map = {
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
    

    for item in items:
        item['ubuilding'] = building_map.get(item['ubuilding'], item['ubuilding'])
        item['image_path'] = item['image_path'].replace("static/", "").replace("\\", "/")


    return render_template('ko/find_ko.html', user_email=user_email,items=items)

@app.route('/ko/register')
def register_ko():
    user_email = session.get('email')
    return render_template('ko/register_ko.html', user_email=user_email)

@app.route('/ko/login_ko', methods=['GET','POST'])
def login_ko():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        if user and user[3] == password:  
            session['user'] = email  
            return redirect(url_for('register_ko'))
        else:
            flash('로그인 실패: 이메일 또는 비밀번호가 올바르지 않습니다.')
            return redirect(url_for('login_ko'))
    return render_template('ko/auth/login_ko.html')

@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect(url_for('auth_bp.login_ko'))

@app.route('/ko/signup')
def signup_ko():
    return render_template('ko/auth/signup_ko.html')

@app.route('/ko/map')
def map_ko():
    return render_template('ko/map_ko.html')

if __name__ == '__main__':
    app.run(debug=True)

