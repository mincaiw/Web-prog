from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime, timedelta

auth_bp = Blueprint('auth_bp', __name__)

USERS_DB_PATH = os.path.abspath('users.db')
YONSEI_DB_PATH = os.path.abspath('instance/yonsei.db')

UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# DB user
def get_users_db():
    conn = sqlite3.connect(USERS_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

#DB found items
def get_yonsei_db():
    conn = sqlite3.connect(YONSEI_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        user_id = request.form['user_id']
        email = request.form['email']
        password = request.form['password']
        hashed_pw = generate_password_hash(password)

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (user_id, email, password) VALUES (?, ?, ?)",
                (user_id, email, hashed_pw)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            flash('이미 존재하는 이메일입니다.')
            return redirect(url_for('auth_bp.signup'))
        finally:
            conn.close()

        flash('회원가입에 성공했습니다!')
        return redirect(url_for('auth_bp.login'))

    return render_template('ko/auth/login_ko.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password'].strip()

        conn = get_users_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['email'] = user['email']
            return redirect(url_for('index_ko'))  
        else:
            flash('이메일 또는 비밀번호가 올바르지 않습니다.')
            return redirect(url_for('auth_bp.login'))
    
    return render_template('ko/auth/login_ko.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('로그아웃되었습니다.')
    return redirect(url_for('auth_bp.login'))

@auth_bp.route('/register_item', methods=['POST'])
def register_item():
    prdt_cl_nm = request.form.get('PRDT_CL_NM')
    start_ymd = request.form.get('START_YMD')
    prdt_nm = request.form.get('PRDT_NM')
    ubuilding = request.form.get('uBuilding')
    description = request.form.get('description')
    image = request.files.get('itemImage')

    image_path = None
    if image and image.filename != '':
        filename = secure_filename(image.filename)
        image_path = os.path.join(UPLOAD_FOLDER, filename)
        image.save(image_path)

    db_path = os.path.abspath('instance/yonsei.db')
    print("💡 DB path used:", db_path)
 
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO found_items (prdt_cl_nm, start_ymd, prdt_nm, ubuilding, description, image_path)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (prdt_cl_nm, start_ymd, prdt_nm, ubuilding, description, image_path))
    conn.commit()
    conn.close()

    flash("습득물이 성공적으로 등록되었습니다.")
    return redirect(url_for('index_ko'))

@auth_bp.route('/ko/register')
def register_ko():
    if 'email' not in session:
        return render_template('ko/register_ko.html', error_message="로그인 후에 등록 기능을 이용하실 수 있습니다.")
    user_email = session['email']
    return render_template('ko/register_ko.html')

@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        conn = get_users_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()

        if user:
            reset_token = str(uuid.uuid4())
            token_expiration = (datetime.now() + timedelta(hours=1)).isoformat()
            cursor.execute("UPDATE users SET reset_token=?, token_expiration=? WHERE email=?", 
                            (reset_token, token_expiration, email))
            conn.commit()
            conn.close()

            reset_link = url_for('auth_bp.reset_password', token=reset_token, _external=True)
    
            return redirect(reset_link)

        else:
            flash("해당 이메일을 찾을 수 없습니다.")  
            return redirect(url_for('auth_bp.forgot_password'))
    return render_template('ko/auth/forgot_password.html') 

@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    conn = get_users_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE reset_token = ?", (token,))
    user = cursor.fetchone()

    if not user or datetime.fromisoformat(user['token_expiration']) < datetime.now():
        conn.close()
        flash("유효하지 않거나 만료된 토큰입니다.")  
        return redirect(url_for('auth_bp.login'))

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        hashed_pw = generate_password_hash(new_password)
        cursor.execute("UPDATE users SET password=?, reset_token=NULL, token_expiration=NULL WHERE reset_token=?",
                       (hashed_pw, token))
        conn.commit()
        conn.close()
        flash("비밀번호가 성공적으로 재설정되었습니다!")  
        return redirect(url_for('auth_bp.login'))

    conn.close()
    return render_template('ko/auth/reset_password.html', token=token)