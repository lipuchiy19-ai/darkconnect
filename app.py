from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO, emit, join_room
import sqlite3
import hashlib
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'supersecretkey_change_it'
socketio = SocketIO(app, cors_allowed_origins="*")

# Настройки загрузки файлов
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm', 'mp3', 'ogg', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('static/stickers', exist_ok=True)

def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        # Таблица пользователей
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE,
            password TEXT,
            name TEXT,
            avatar TEXT DEFAULT 'default.png',
            phone TEXT,
            email TEXT
        )''')
        # Таблица стены (посты)
        conn.execute('''CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            content TEXT,
            image TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')
        # Таблица сообщений
        conn.execute('''CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user INTEGER,
            to_user INTEGER,
            content TEXT,
            file_url TEXT,
            is_video_note BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''")
        # Добавим демо-пользователя
        demo_pass = hashlib.sha256("123".encode()).hexdigest()
        conn.execute("INSERT OR IGNORE INTO users (id, login, password, name) VALUES (1, 'demo', ?, 'Демо ВК')", (demo_pass,))
        conn.execute("INSERT OR IGNORE INTO users (id, login, password, name) VALUES (2, 'alice', ?, 'Алиса')", (demo_pass,))
        conn.commit()
init_db()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('feed'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE login = ? AND password = ?', (login, password)).fetchone()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['name']
            return redirect(url_for('feed'))
        return 'Ошибка входа', 403
    return '''
    <form method="post">
        <input name="login" placeholder="Логин (demo или alice)" required><br>
        <input name="password" type="password" placeholder="Пароль (123)" required><br>
        <button>Войти</button>
    </form>
    <a href="/register">Регистрация</a>
    '''

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Здесь нужно добавить отправку кода на почту/SMS. Для демо - просто проверка
        login = request.form['login']
        phone = request.form.get('phone')
        email = request.form.get('email')
        # Код подтверждения (заглушка - "1111")
        code = request.form.get('code')
        if code != '1111': # В реальном проекте шлем через SMTP/SMS API
            return "Неверный код подтверждения. Демо-код: 1111"
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        db = get_db()
        try:
            db.execute('INSERT INTO users (login, password, name, phone, email) VALUES (?, ?, ?, ?, ?)',
                       (login, password, login, phone, email))
            db.commit()
            return redirect(url_for('login'))
        except:
            return "Логин занят"
    return '''
    <form method="post">
        <input name="login" placeholder="Логин" required><br>
        <input name="phone" placeholder="Телефон +79111111111"><br>
        <input name="email" placeholder="Email"><br>
        <input name="password" type="password" placeholder="Пароль" required><br>
        <input name="code" placeholder="Код из SMS/почты (демо: 1111)"><br>
        <button>Зарегистрироваться</button>
        <p>В демо-версии код всегда 1111</p>
    </form>
    '''

@app.route('/feed', methods=['GET', 'POST'])
def feed():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    if request.method == 'POST':
        content = request.form['content']
        file = request.files.get('image')
        filename = None
        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        db.execute('INSERT INTO posts (user_id, content, image) VALUES (?, ?, ?)',
                   (session['user_id'], content, filename))
        db.commit()
        return redirect(url_for('feed'))
    posts = db.execute('''
        SELECT posts.*, users.name FROM posts 
        JOIN users ON posts.user_id = users.id 
        ORDER BY posts.created_at DESC
    ''').fetchall()
    return render_template_string(HTML_TEMPLATE, posts=posts, username=session['username'])

# Обработка сообщений в реальном времени (WebSocket)
@socketio.on('send_message')
def handle_message(data):
    db = get_db()
    db.execute('INSERT INTO messages (from_user, to_user, content) VALUES (?, ?, ?)',
               (session.get('user_id'), 1, data['msg'])) # ЛС с демо-пользователем
    db.commit()
    emit('new_message', {'msg': data['msg'], 'from': session.get('username')}, broadcast=True)

# Роут для загрузки стикеров (сделаем простой)
@app.route('/upload_sticker', methods=['POST'])
def upload_sticker():
    if 'user_id' not in session: return 'no auth', 401
    file = request.files['sticker']
    filename = secure_filename(file.filename)
    file.save(f'static/stickers/{filename}')
    return jsonify({'url': f'/static/stickers/{filename}'})

# Глобальный HTML (объединим с JS/CSS)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>DarkConnect</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <link rel="stylesheet" href="/static/style.css">
    <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>
<div class="app">
    <div class="sidebar">
        <h2>DarkNet</h2>
        <nav>
            <a href="/feed">Стена</a>
            <a href="/chat">Чат (стикеры/кружки)</a>
            <a href="/gallery">Галерея</a>
        </nav>
        <div>Привет, {{ username }}<br><a href="/logout">Выйти</a></div>
    </div>
    <div class="main">
        {% block content %}{% endblock %}
    </div>
</div>
<script src="/static/script.js"></script>
</body>
</html>
'''

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Страница чата
@app.route('/chat')
def chat():
    return render_template_string('''
    {% extends "base.html" %}
    {% block content %}
    <div class="chat-header">Общий чат (как Telegram)</div>
    <div id="messages" style="height:400px; overflow-y:scroll; background:#1e1e1e; padding:10px;"></div>
    <div class="message-input">
        <button id="emojiBtn">:)</button>
        <button id="stickerBtn">Стикер</button>
        <input type="file" id="fileInput" accept="image/*,video/*,audio/*">
        <button id="recordVideo">Кружок</button>
        <input type="text" id="msgInput" placeholder="Сообщение..." autocomplete="off">
        <button id="sendBtn">Отправить</button>
    </div>
    <div id="stickerPanel" style="display:none; background:#2c2c2c; padding:10px;">
        <button class="sticker" data-url="/static/stickers/cat.png">Стикер1</button>
        <button class="sticker" data-url="/static/stickers/dog.png">Стикер2</button>
        <form method="post" action="/upload_sticker" enctype="multipart/form-data" style="display:inline;">
            <input type="file" name="sticker" accept="image/png">
            <button>Загрузить свой стикер</button>
        </form>
    </div>
    {% endblock %}
    ''', username=session['username'])

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)