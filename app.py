import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "vendor"))

from flask import Flask, render_template, request, redirect, url_for, flash  
from flask_login import login_required, current_user, LoginManager
from flask_cors import CORS
from auth import auth_bp
from dotenv import load_dotenv
import requests

load_dotenv()
NAVER_CLIENT_ID=os.getenv("udhwj5en73")
NAVER_CLIENT_SECRET=os.getenv("gL2gWzBkk0bOSN8TnYdpbMRNDFVXPnDP5wdixzgM")

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
    return render_template('en/register_en.html')

# Korean page
@app.route('/ko')
def index_ko():
    return render_template('ko/index_ko.html')

@app.route('/ko/find')
def find_ko():
    return render_template('ko/find_ko.html')

@app.route('/ko/register')
def register_ko():
    return render_template('ko/register_ko.html')

@app.route('/ko/login')
def login_ko():
    return render_template('ko/auth/login_ko.html')

@app.route('/ko/signup')
def signup_ko():
    return render_template('ko/auth/signup_ko.html')

@app.route('/ko/map')
def map_ko():
    return render_template('ko/map_ko.html')

@app.route('/ch')
def index_ch():
    return render_template('ch/index_ch.html')

if __name__ == '__main__':
    app.run(debug=True)

