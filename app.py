from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests
import json
import os
import re
from dotenv import load_dotenv
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

load_dotenv()
key = os.getenv('SECRET_KEY')

Api_key = os.getenv('API_KEY')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-change-in-production'

# --- Flask-Login Setup ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- User Model and Store ---
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

# In-memory user store loaded from environment variables
users = {
    '1': User(
        id='1',
        username=os.getenv('CHAT_USERNAME'),
        password=os.getenv('CHAT_PASSWORD')
    )
}

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

def format_gemini_response(text):
    """
    Enhanced formatting function to make Gemini responses look like GPT output
    """
    if not text:
        return text
    
    # Clean up the text first
    formatted_text = text.strip()
    
    # Handle code blocks (```language ... ```)
    formatted_text = re.sub(
        r'```(\w+)?\n?(.*?)```', 
        r'<div class="code-block"><div class="code-header"><span>\1</span><button class="copy-btn" onclick="copyCode(this)"><svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>Copy</button></div><pre><code>\2</code></pre></div>', 
        formatted_text, 
        flags=re.DOTALL
    )
    
    # Handle inline code (`code`)
    formatted_text = re.sub(r'`([^`]+)`', r'<code class="inline-code">\1</code>', formatted_text)
    
    # Handle bold text (**text** -> <strong>text</strong>)
    formatted_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', formatted_text)
    
    # Handle italic text (*text* -> <em>text</em>)
    formatted_text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', formatted_text)
    
    # Handle numbered lists (1. item)
    formatted_text = re.sub(r'^(\d+)\.\s+(.+)$', r'<div class="numbered-item"><span class="number">\1.</span>\2</div>', formatted_text, flags=re.MULTILINE)
    
    # Handle bullet points (- item or * item)
    formatted_text = re.sub(r'^[-*]\s+(.+)$', r'<div class="bullet-item"><span class="bullet">•</span>\1</div>', formatted_text, flags=re.MULTILINE)
    
    # Handle headers (## Header -> <h3>Header</h3>)
    formatted_text = re.sub(r'^###\s+(.+)$', r'<h4>\1</h4>', formatted_text, flags=re.MULTILINE)
    formatted_text = re.sub(r'^##\s+(.+)$', r'<h3>\1</h3>', formatted_text, flags=re.MULTILINE)
    formatted_text = re.sub(r'^#\s+(.+)$', r'<h2>\1</h2>', formatted_text, flags=re.MULTILINE)
    
    # Handle line breaks - convert double newlines to paragraph breaks
    formatted_text = re.sub(r'\n\n+', '</p><p>', formatted_text)
    
    # Handle single line breaks within paragraphs
    formatted_text = re.sub(r'(?<!>)\n(?!<)', '<br>', formatted_text)
    
    # Wrap in paragraph tags if not already wrapped
    if not formatted_text.startswith('<'):
        formatted_text = f'<p>{formatted_text}</p>'
    
    # Clean up empty paragraphs
    formatted_text = re.sub(r'<p>\s*</p>', '', formatted_text)
    
    return formatted_text

# --- Auth Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_to_login = next((user for user in users.values() if user.username == username), None)
        if user_to_login and user_to_login.password == password:
            login_user(user_to_login)
            return redirect(url_for('index'))
        # TODO: Add flash message for failed login
        return '<h1>Invalid username or password</h1>'
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- Application Routes ---
@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
@login_required
def ask():
    user_question = request.json.get('question')
    if not user_question:
        return jsonify({"error": "No question provided"}), 400

    url = Api_key

    payload = json.dumps({
        "question": user_question
    })
    headers = {
        'Content-Type': 'application/json',
        'Cookie': '.Tunnels.Relay.WebForwarding.Cookies=CfDJ8Cs4yarcs6pKkdu0hlKHsZtRO8A8h7IjvZlYpgy2MJleI4sKTNaCxf-_XAbzdKCEsCtOjlTRb0DVuw7OiyJy50BVhGHbGfWb6FZ2gAZEtxC0uH_-iBDeoB7_NvW6qOEGsxGTzFTfKh2-bC5J2xcISPs0--b5kCkzB0bHm40VpmNVXbmpglKuVfpsfIlTCsM1oNKl-L5o_SFo7Fcaq3iHi06ozpJFbkarToWPPAsPvNT5D4sz2FCXr-3rDLEvp7t6FogMrX36f86dGG6s_twbBZYcCt8s8qfSKUwgzhiU--FfalYbVkBU4SwJ1WMk7ldg4QuzzpO3iy8CkFwaCa8Q34Us41ntL9CPAQ5P0OikIRZOgpm_wpA-Im8cTHdytEqZZMHVj_Hbq-q4tGjcF4M85GK0x_U-Bt9QPlzhXuaCstZ4eVjNkuw5nhi1a24yh0-Pi7MlEGwMiEgBkQDMzkPVNxrA1f1mtBKKgNsgBrvxyltT5N4mZACmEcfO1ULNyqvDL3BiXVmu4Q91_cnQAd3n6t2q9NB8zAW3bel3nboT2ZRlUoiVsAQMg6ge58qkGETsuI7rY7z3GOCaGcbjfNRVBoFjGnEJJGjFwB4YOoZ9EQixS7NN46a5H0tovsghLoMJ-niLXh6nBbzbtcSNi-6_PFYhcdNV3hKLVg7KNbzSK9njKDKxoF_k77_ZpRWW7vwyTdt6-T7UnXrpnQj9C6trMCIWg-nA-FatXpEzeVB9N3v60EfXe_IEpCOpT5njaszVU5RP7BV9o69MgV_Nqe_tXugKv5l5SbRyqcEgKAlDEhcp2Z9BVZTZhJ6E4-B03RykyRvu5dBLLd0TmG9HXwTRuIKspPPvn9W4Tpeoh-7T612J1G8BrP9AiMQLosSmMpWiIiBpZg2FqQwe8r9eA8LpCktNAisBNwt28MOf6vJi52Ah'
    }

    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        response.raise_for_status()  # Raise an exception for bad status codes
        api_response = response.json()
        raw_answer = api_response.get("answer_html", "Sorry, I couldn't get an answer.")
        
        # Enhanced formatting for GPT-like output
        formatted_answer = format_gemini_response(raw_answer)

        return jsonify({"answer": formatted_answer})
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
