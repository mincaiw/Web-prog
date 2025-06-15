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

# DB用户辅助函数
def get_users_db():
    conn = sqlite3.connect(USERS_DB_PATH)
    conn.row_factory = sqlite3.Row # 允许按名称访问列
    return conn

# DB失物招领物品辅助函数
def get_yonsei_db():
    conn = sqlite3.connect(YONSEI_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# 统一注册路由
@auth_bp.route('/<string:lang_code>/signup', methods=['GET', 'POST'])
def signup(lang_code):
    if request.method == 'POST':
        user_id = request.form['user_id'].strip() # 从表单获取user_id
        email = request.form['email'].strip()
        password = request.form['password'].strip()
        
        if not user_id or not email or not password:
            if lang_code == 'ko':
                flash('모든 필드를 채워주세요.', 'error')
            else:
                flash('Please fill in all fields.', 'error')
            return render_template(f'{lang_code}/auth/signup_{lang_code}.html', lang=lang_code, title="Sign Up")

        hashed_pw = generate_password_hash(password)

        conn = get_users_db() # 使用辅助函数
        cursor = conn.cursor()
        try:
            # 检查用户ID或电子邮件是否已存在
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
            return redirect(url_for('auth_bp.login', lang_code=lang_code)) # 重定向到统一登录路由
        except sqlite3.Error as e:
            print(f"Database error during signup: {e}")
            if lang_code == 'ko':
                flash('회원가입 중 오류가 발생했습니다. 다시 시도해주세요.', 'error')
            else:
                flash('An error occurred during registration. Please try again.', 'error')
            return render_template(f'{lang_code}/auth/signup_{lang_code}.html', lang=lang_code, title="Sign Up")
        finally:
            if conn: # 确保即使发生错误，连接也已关闭
                conn.close()
    
    # 对于GET请求，渲染特定的注册模板
    return render_template(f'{lang_code}/auth/signup_{lang_code}.html', lang=lang_code, title="Sign Up")


# 统一登录路由
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

        # 使用check_password_hash检查密码
        if user and check_password_hash(user['password'], password):
            session['email'] = user['email']
            session['user_id'] = user['user_id'] 
            # 重定向到主索引页（应用程序的索引路由）
            return redirect(url_for('index', lang_code=lang_code))  
        else:
            if lang_code == 'ko':
                flash('이메일 또는 비밀번호가 올바르지 않습니다.', 'error')
            else:
                flash('Incorrect Email or Password.', 'error')
            # 登录失败时重新渲染登录页面
            return render_template(f'{lang_code}/auth/login_{lang_code}.html', lang=lang_code, title="Login")
    
    return render_template(f'{lang_code}/auth/login_{lang_code}.html', lang=lang_code, title="Login")

# 注销路由
@auth_bp.route('/logout/<string:lang_code>')
def logout(lang_code):
    session.clear()
    if lang_code == 'ko':
        flash('로그아웃되었습니다.', 'info')
    else:
        flash('You have been logged out.', 'info')
    return redirect(url_for('auth_bp.login', lang_code=lang_code)) # FIXED: 确保lang_code作为关键字参数传递

# 物品注册路由
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
        unique_filename = str(uuid.uuid4()) + "_" + filename # 生成唯一文件名
        image_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        image.save(image_path)
        image_path = os.path.join('static', 'uploads', unique_filename).replace("\\", "/") # 存储可网页访问的路径

    conn = get_yonsei_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO found_items (prdt_cl_nm, start_ymd, prdt_nm, ubuilding, image_path, user_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (prdt_cl_nm, start_ymd, prdt_nm, ubuilding, image_path, user_id))
        conn.commit()
        flash("습득물이 성공적으로 등록되었습니다.", 'success')
    except sqlite3.Error as e:
        print(f"Database error during item registration: {e}")
        flash("습득물 등록 중 오류가 발생했습니다.", 'error')
    finally:
        if conn:
            conn.close()

    current_lang = session.get('lang', 'ko')
    if request.referrer and '/en/' in request.referrer:
        current_lang = 'en'
    
    return redirect(url_for('index', lang_code=current_lang))

# 物品注册页面路由（实际渲染注册页面的路由）
@auth_bp.route('/ko/register')
def register_ko():
    # 从环境中获取Naver客户端ID，并传递给模板，因为页面包含地图功能
    naver_client_id = os.getenv("NAVER_CLIENT_ID")
    if 'email' not in session:
        flash("로그인 후에 등록 기능을 이용하실 수 있습니다.", 'error')
        return redirect(url_for('auth_bp.login', lang_code='ko'))
    user_email = session.get('email') # 获取用户email
    return render_template('ko/register_ko.html', lang='ko', title="Register Item", user_email=user_email, naver_client_id=naver_client_id)

@auth_bp.route('/en/register')
def register_en():
    # 从环境中获取Naver客户端ID，并传递给模板，因为页面包含地图功能
    naver_client_id = os.getenv("NAVER_CLIENT_ID")
    if 'email' not in session:
        flash("Please log in to register an item.", 'error')
        return redirect(url_for('auth_bp.login', lang_code='en'))
    user_email = session.get('email') # 获取用户email
    return render_template('en/register_en.html', lang='en', title="Register Item", user_email=user_email, naver_client_id=naver_client_id)


# 忘记密码路由
@auth_bp.route('/ko/forgot_password', methods=['GET', 'POST'])
def forgot_password_ko():
    if request.method == 'POST':
        email = request.form.get('email').strip()
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
            # FIXED: 确保reset_password的url_for包含lang_code参数
            reset_link = url_for('auth_bp.reset_password', token=reset_token, lang_code='ko', _external=True)
            flash("비밀번호 재설정 링크가 이메일로 전송되었습니다.", 'info')
            return redirect(reset_link)
        else:
            flash("해당 이메일을 찾을 수 없습니다.", 'error')  
            return render_template('ko/auth/forgot_password_ko.html', lang='ko', title="Forgot Password")
    return render_template('ko/auth/forgot_password_ko.html', lang='ko', title="Forgot Password") 

@auth_bp.route('/en/forgot_password', methods=['GET', 'POST'])
def forgot_password_en():
    if request.method == 'POST':
        email = request.form.get('email').strip()
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
            # FIXED: 确保reset_password的url_for包含lang_code参数
            reset_link = url_for('auth_bp.reset_password', token=reset_token, lang_code='en', _external=True)
            flash("Password reset link has been sent to your email.", 'info')
            return redirect(reset_link)
        else:
            flash("Email not found.", 'error')  
            return render_template('en/auth/forgot_password_en.html', lang='en', title="Forgot Password")
    return render_template('en/auth/forgot_password_en.html', lang='en', title="Forgot Password") 

# 重置密码路由（统一）
@auth_bp.route('/<string:lang_code>/reset_password/<token>', methods=['GET', 'POST']) # 统一的reset_password路由
def reset_password(lang_code, token): # lang_code现在显式地作为函数参数
    conn = get_users_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE reset_token = ?", (token,))
    user = cursor.fetchone()

    if not user or datetime.fromisoformat(user['token_expiration']) < datetime.now():
        conn.close()
        if lang_code == 'ko':
            flash("유효하지 않거나 만료된 토큰입니다.", 'error')  
            return redirect(url_for('auth_bp.login', lang_code='ko'))
        else:
            flash("Invalid or expired token.", 'error')  
            return redirect(url_for('auth_bp.login', lang_code='en'))

    if request.method == 'POST':
        new_password = request.form.get('new_password').strip()
        if not new_password:
            if lang_code == 'ko':
                flash("새 비밀번호를 입력해주세요.", 'warning')
            else:
                flash("Please enter the new password.", 'warning')
            conn.close()
            # FIXED: 确保渲染模板时lang_code作为关键字参数传递
            return render_template(f'{lang_code}/auth/reset_password_{lang_code}.html', token=token, lang=lang_code, title="Reset Password")
            
        hashed_pw = generate_password_hash(new_password)
        cursor.execute("UPDATE users SET password=?, reset_token=NULL, token_expiration=NULL WHERE reset_token=?",
                       (hashed_pw, token))
        conn.commit()
        conn.close()
        if lang_code == 'ko':
            flash("비밀번호가 성공적으로 재설정되었습니다!", 'success')  
            return redirect(url_for('auth_bp.login', lang_code=lang_code)) # FIXED: 确保lang_code作为关键字参数传递
        else:
            flash("Your password has been successfully reset!", 'success')  
            return redirect(url_for('auth_bp.login', lang_code=lang_code)) # FIXED: 确保lang_code作为关键字参数传递

    conn.close()
    # FIXED: 确保渲染模板时lang_code作为关键字参数传递
    return render_template(f'{lang_code}/auth/reset_password_{lang_code}.html', token=token, lang=lang_code, title="Reset Password")
