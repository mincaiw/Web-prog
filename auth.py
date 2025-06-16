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

def get_users_db():
    conn = sqlite3.connect(USERS_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_yonsei_db():
    conn = sqlite3.connect(YONSEI_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@auth_bp.route('/<string:lang_code>/signup', methods=['GET', 'POST'])
def signup(lang_code):
    if request.method == 'POST':
        user_id = request.form['user_id'].strip()
        email = request.form['email'].strip()
        password = request.form['password'].strip()
        
        if not user_id or not email or not password:
            if lang_code == 'ko':
                flash('모든 필드를 채워주세요.', 'error')
            else:
                flash('Please fill in all fields.', 'error')
            return render_template(f'{lang_code}/auth/signup_{lang_code}.html', lang=lang_code, title="Sign Up")

        hashed_pw = generate_password_hash(password)

        conn = get_users_db()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT * FROM users WHERE user_id = ? OR email = ?', (user_id, email))
            existing_user = cursor.fetchone()
            if existing_user:
                if lang_code == 'ko':
                    flash('이미 존재하는 사용자 ID 또는 이메일입니다. 다른 정보를 사용해주세요.', 'error')
                else:
                    flash('User ID or email already exists. Please use different ones.', 'error')
                return render_template(f'{lang_code}/auth/signup_{lang_code}.html', lang=lang_code, title="Sign Up")

            cursor.execute(
                "INSERT INTO users (user_id, email, password) VALUES (?, ?, ?)",
                (user_id, email, hashed_pw)
            )
            conn.commit()
            if lang_code == 'ko':
                flash('회원가입에 성공했습니다! 로그인해주세요.', 'success')
            else:
                flash('You have signed up successfully! Please log in.', 'success')
            return redirect(url_for('auth_bp.login', lang_code=lang_code))
        except sqlite3.Error as e:
            print(f"Database error during signup: {e}")
            if lang_code == 'ko':
                flash('회원가입 중 오류가 발생했습니다. 다시 시도해주세요.', 'error')
            else:
                flash('An error occurred during registration. Please try again.', 'error')
            return render_template(f'{lang_code}/auth/signup_{lang_code}.html', lang=lang_code, title="Sign Up")
        finally:
            if conn:
                conn.close()
    
    return render_template(f'{lang_code}/auth/signup_{lang_code}.html', lang=lang_code, title="Sign Up")

@auth_bp.route('/<string:lang_code>/login', methods=['GET', 'POST'])
def login(lang_code):
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
            session['user_id'] = user['user_id']
            return redirect(url_for('index', lang_code=lang_code))
        else:
            if lang_code == 'ko':
                flash('이메일 또는 비밀번호가 올바르지 않습니다.', 'error')
            else:
                flash('Incorrect Email or Password.', 'error')
            return render_template(f'{lang_code}/auth/login_{lang_code}.html', lang=lang_code, title="Login")
    
    return render_template(f'{lang_code}/auth/login_{lang_code}.html', lang=lang_code, title="Login")

@auth_bp.route('/logout/<string:lang_code>')
def logout(lang_code):
    session.clear()
    if lang_code == 'ko':
        flash('로그아웃되었습니다.', 'info')
    else:
        flash('You have been logged out.', 'info')
    return redirect(url_for('auth_bp.login', lang_code=lang_code))

@auth_bp.route('/register_item', methods=['POST'])
def register_item():
    prdt_cl_nm = request.form.get('PRDT_CL_NM')
    start_ymd = request.form.get('START_YMD')
    prdt_nm = request.form.get('PRDT_NM')
    ubuilding = request.form.get('uBuilding')
    image = request.files.get('itemImage')
    user_id = session.get('user_id')

    image_path = None
    if image and image.filename:
        filename = secure_filename(image.filename or "")
        unique_filename = str(uuid.uuid4()) + "_" + filename
        image_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        image.save(image_path)
        image_path = os.path.join('static', 'uploads', unique_filename).replace("\\", "/")

    conn = get_yonsei_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO found_items (prdt_cl_nm, start_ymd, prdt_nm, ubuilding, image_path, user_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (prdt_cl_nm, start_ymd, prdt_nm, ubuilding, image_path, user_id))
        conn.commit()
        if session.get('lang', 'ko') == 'ko':
            flash("습득물이 성공적으로 등록되었습니다.", 'success')
        else:
            flash("Item successfully registered.", 'success')
    except sqlite3.Error as e:
        print(f"Database error during item registration: {e}")
        if session.get('lang', 'ko') == 'ko':
            flash("습득물 등록 중 오류가 발생했습니다.", 'error')
        else:
            flash("An error occurred during item registration.", 'error')
    finally:
        if conn:
            conn.close()

    current_lang = session.get('lang', 'ko')
    return redirect(url_for('find', lang_code=current_lang))

@auth_bp.route('/ko/register')
def register_ko():
    naver_client_id = os.getenv("NAVER_CLIENT_ID")
    user_email = session.get('email')
    if not user_email:
        flash("로그인 후에 등록 기능을 이용하실 수 있습니다.", 'error')
        return redirect(url_for('auth_bp.login', lang_code='ko'))
    return render_template('ko/register_ko.html', lang='ko', title="Register Item", user_email=user_email, naver_client_id=naver_client_id)

@auth_bp.route('/en/register')
def register_en():
    naver_client_id = os.getenv("NAVER_CLIENT_ID")
    user_email = session.get('email')
    if not user_email:
        flash("Please log in to register an item.", 'error')
        return redirect(url_for('auth_bp.login', lang_code='en'))
    return render_template('en/register_en.html', lang='en', title="Register Item", user_email=user_email, naver_client_id=naver_client_id)

@auth_bp.route('/<string:lang_code>/forgot_password', methods=['GET', 'POST'])
def forgot_password(lang_code):
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        
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
            if lang_code == 'ko':
                flash("비밀번호 재설정 링크가 이메일로 전송되었습니다.", 'info')
            else:
                flash("Password reset link has been sent to your email.", 'info')
            reset_link = url_for('auth_bp.reset_password', token=reset_token, lang_code=lang_code, _external=True)
            conn.close()
            return render_template(f'{lang_code}/auth/forgot_password_{lang_code}.html', lang=lang_code, title="Forgot Password")
        else:
            if lang_code == 'ko':
                flash("해당 이메일을 찾을 수 없습니다.", 'error')
            else:
                flash("Email not found.", 'error')
            conn.close()
            return render_template(f'{lang_code}/auth/forgot_password_{lang_code}.html', lang=lang_code, title="Forgot Password")
    
    return render_template(f'{lang_code}/auth/forgot_password_{lang_code}.html', lang=lang_code, title="Forgot Password")

@auth_bp.route('/<string:lang_code>/reset_password', methods=['GET', 'POST'])
def reset_password(lang_code):
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        new_password = request.form.get('new_password', '').strip()

        if not email or not new_password:
            if lang_code == 'ko':
                flash("이메일과 새 비밀번호를 모두 입력해주세요.", 'warning')
            else:
                flash("Please enter both email and new password.", 'warning')
            return render_template(f'{lang_code}/auth/reset_password_{lang_code}.html', lang=lang_code, title="Reset Password")

        conn = get_users_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()

        if user:
            hashed_pw = generate_password_hash(new_password)
            cursor.execute("UPDATE users SET password=? WHERE email=?", (hashed_pw, email))
            conn.commit()
            conn.close()
            if lang_code == 'ko':
                flash("비밀번호가 성공적으로 재설정되었습니다! 로그인해주세요.", 'success')
            else:
                flash("Your password has been successfully reset! Please log in.", 'success')
            return redirect(url_for('auth_bp.login', lang_code=lang_code))
        else:
            conn.close()
            if lang_code == 'ko':
                flash("해당 이메일을 찾을 수 없습니다. 다시 시도해주세요.", 'error')
            else:
                flash("Email not found. Please try again.", 'error')
            return render_template(f'{lang_code}/auth/reset_password_{lang_code}.html', lang=lang_code, title="Reset Password")
    
    return render_template(f'{lang_code}/auth/reset_password_{lang_code}.html', lang=lang_code, title="Reset Password")