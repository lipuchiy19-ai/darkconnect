# -*- coding: utf-8 -*-
from flask import Flask, render_template_string, request, redirect, url_for, session
import sqlite3
import hashlib
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here_change_it'

# Простая HTML-страница для чата
CHAT_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>DarkConnect - Чат</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{background:#0a0a0a;color:#e0e0e0;font-family:system-ui}
        .app{display:flex;min-height:100vh}
        .sidebar{width:250px;background:#1e1e1e;padding:20px;border-right:1px solid #333}
        .main{flex:1;padding:20px}
        .message{background:#2c2c2c;padding:10px;margin:10px 0;border-radius:12px}
        .input-area{display:flex;gap:10px;margin-top:20px}
        input,button{padding:10px;border-radius:20px;border:none}
        input{flex:1;background:#2a2a2a;color:white}
        button{background:#3a3a3a;color:white;cursor:pointer}
        .nav-link{display:block;padding:10px;color:#e0e0e0;text-decoration:none}
        h2{color:#4c9aff}
    </style>
</head>
<body>
<div class="app">
    <div class="sidebar">
        <h2>DarkConnect</h2>
        <a href="/feed" class="nav-link">Стена</a>
        <a href="/chat" class="nav-link">Чат</a>
        <a href="/gallery" class="nav-link">Галерея</a>
        <div style="margin-top:50px">
            Привет, {{ username }}<br>
            <a href="/logout" style="color:#4c9aff">Выйти</a>
        </div>
    </div>
    <div class="main">
        <h1>Чат</h1>
        <div id="messages" style="height:400px;overflow-y:auto;background:#1e1e1e;padding:10px;border-radius:12px">
            <div class="message">Добро пожаловать в чат!</div>
        </div>
        <div class="input-area">
            <input type="text" id="msgInput" placeholder="Сообщение...">
            <button onclick="sendMessage()">Отправить</button>
        </div>
    </div>
</div>
<script>
    function sendMessage() {
        let input = document.getElementById('msgInput');
        let msg = input.value;
        if(msg) {
            let div = document.createElement('div');
            div.className = 'message';
            div.innerHTML = '<b>Я:</b> ' + msg;
            document.getElementById('messages').appendChild(div);
            input.value = '';
        }
    }
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return redirect('/login')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        if request.form['login'] == 'demo' and request.form['password'] == '123':
            session['user_id'] = 1
            session['username'] = 'Демо'
            return redirect('/chat')
        return 'Ошибка входа. Используй demo / 123'
    return '''
    <div style="max-width:400px;margin:100px auto;background:#1e1e1e;padding:30px;border-radius:12px">
        <h2>Вход в DarkConnect</h2>
        <form method="post">
            <input name="login" placeholder="Логин (demo)" required><br><br>
            <input name="password" type="password" placeholder="Пароль (123)" required><br><br>
            <button type="submit">Войти</button>
        </form>
        <p style="margin-top:20px"><a href="/register">Регистрация</a></p>
    </div>
    '''

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        if request.form.get('code') == '1111':
            return 'Регистрация успешна! <a href="/login">Войти</a>'
        return 'Неверный код (демо: 1111)'
    return '''
    <div style="max-width:400px;margin:100px auto;background:#1e1e1e;padding:30px;border-radius:12px">
        <h2>Регистрация</h2>
        <form method="post">
            <input name="login" placeholder="Логин" required><br><br>
            <input name="email" placeholder="Email"><br><br>
            <input name="phone" placeholder="Телефон"><br><br>
            <input name="password" type="password" placeholder="Пароль" required><br><br>
            <input name="code" placeholder="Код (1111)" required><br><br>
            <button type="submit">Зарегистрироваться</button>
        </form>
    </div>
    '''

@app.route('/feed')
def feed():
    if 'user_id' not in session:
        return redirect('/login')
    return '''
    <div style="max-width:800px;margin:50px auto;background:#1e1e1e;padding:20px;border-radius:12px">
        <h1>Стена</h1>
        <div style="background:#2c2c2c;padding:15px;margin:10px 0;border-radius:12px">
            <b>Админ</b>: Добро пожаловать в DarkConnect!
        </div>
        <div style="background:#2c2c2c;padding:15px;margin:10px 0;border-radius:12px">
            <b>Демо</b>: Это упрощенная социальная сеть
        </div>
        <a href="/chat">Перейти в чат</a>
    </div>
    '''

@app.route('/chat')
def chat():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template_string(CHAT_PAGE, username=session.get('username', 'Гость'))

@app.route('/gallery')
def gallery():
    if 'user_id' not in session:
        return redirect('/login')
    return '''
    <div style="max-width:800px;margin:50px auto;background:#1e1e1e;padding:20px;border-radius:12px">
        <h1>Галерея</h1>
        <p>Тут будут фото и видео (функция в разработке)</p>
        <a href="/chat">Вернуться в чат</a>
    </div>
    '''

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)