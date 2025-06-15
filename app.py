import sys, os, sqlite3
from functools import wraps
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "vendor"))

from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from flask_cors import CORS
from auth import auth_bp # 假设 auth.py 包含 auth_bp

from dotenv import load_dotenv

load_dotenv()
# 修正os.getenv调用的变量名
# 确保这些环境变量在您的.env文件中设置
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET") # 如果在其他地方需要，也要确保设置此项

def get_found_items_from_db(): # 重命名以避免与路由名称混淆
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

app = Flask(__name__, static_folder='static', template_folder='templates') # 显式设置模板文件夹
app.secret_key = os.getenv("SECRET_KEY", "yonsei_uni_140_default_secret") # 使用环境变量设置密钥，提供默认值
CORS(app)

app.register_blueprint(auth_bp, url_prefix='/auth') # 所有认证路由现在都在/auth下

# 在每个请求之前，根据URL路径确定语言
@app.before_request
def set_language_for_g():
    # 默认语言是韩语
    g.lang = 'ko'
    # 检查URL路径是否以'/en'开头
    if request.path.startswith('/en/'):
        g.lang = 'en'
    # 对于根路径'/'，重定向到默认语言的索引页（由home()处理）
    # 重要：确保此逻辑正确设置所有路由（包括蓝图路由）的g.lang
    elif request.path.startswith('/auth/ko/'):
        g.lang = 'ko'
    elif request.path.startswith('/auth/en/'):
        g.lang = 'en'
    # 如果是根路径，则始终设置为'ko'并重定向（由home()处理）
    # 否则，如果未找到'/en/'，g.lang将默认为'ko'，这没问题。
    session['lang'] = g.lang # 将语言保存到session，以便flash消息等使用

# 辅助函数，用于从session获取用户email
def get_current_user_email():
    return session.get('email')

# 合并的索引路由：处理/和/<lang_code>/
@app.route('/')
def home():
    # 重定向到默认的韩语索引页
    return redirect(url_for('index', lang_code='ko'))

@app.route('/<string:lang_code>/')
def index(lang_code):
    user_email = get_current_user_email()
    # 将确定的语言传递给base模板
    return render_template('base.html', user_email=user_email, lang=lang_code, title="Home")

@app.route('/<string:lang_code>/find')
def find(lang_code):
    user_email = get_current_user_email()
    items = get_found_items_from_db() # 调用函数获取物品

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

    building_map_en = { # 建筑物名称的英文翻译示例
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

    # 根据语言选择合适的地图
    building_map = building_map_ko if lang_code == 'ko' else building_map_en
    
    for item in items:
        # 使用.get()并带回退值，以避免如果ubuilding代码不在地图中时出现KeyError
        item['ubuilding'] = building_map.get(item['ubuilding'], item['ubuilding'])
        # 确保图片路径已正确格式化以便网页访问
        if item['image_path']:
            # 调整路径以进行网页访问 - 删除'static/'，因为url_for('static', ...)会添加它
            # 并处理Windows路径中的反斜杠，将其转换为正斜杠
            item['image_path'] = item['image_path'].replace("static/", "").replace("\\", "/")
        else:
            item['image_path'] = 'images/placeholder.png' # 缺少图片时的回退

    # 根据语言渲染正确的查找页面模板
    if lang_code == 'ko':
        return render_template('ko/find_ko.html', user_email=user_email, items=items, lang=lang_code, title="습득물 검색")
    else:
        return render_template('en/find_en.html', user_email=user_email, items=items, lang=lang_code, title="Search Found Items")

# 这个路由现在只是简单地重定向到蓝图的注册页面。
# 实际的渲染由auth_bp.register_ko/en处理。
@app.route('/<string:lang_code>/register')
def register(lang_code):
    return redirect(url_for(f'auth_bp.register_{lang_code}'))


@app.route('/<string:lang_code>/map')
def map(lang_code):
    naver_client_id = os.getenv("NAVER_CLIENT_ID") # 从环境中获取客户端ID
    if lang_code == 'ko':
        return render_template('ko/map_ko.html', lang=lang_code, title="연세대학교 국제캠퍼스 지도", naver_client_id=naver_client_id)
    else: # English
        return render_template('en/map_en.html', lang=lang_code, title="Yonsei University International Campus Map", naver_client_id=naver_client_id)

# 辅助函数，用于初始化用户数据库（如果不存在）
def init_db():
    conn = None
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        # 重要：确保user_id和email是UNIQUE的，以防止重复
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

# 辅助函数，用于初始化found_items数据库（如果不存在）
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
    init_db() # 应用程序启动时初始化用户数据库
    init_yonsei_db() # 初始化found_items数据库
    app.run(debug=True)
