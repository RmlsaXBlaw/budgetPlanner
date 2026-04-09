from flask import Flask, request, render_template, jsonify, redirect, url_for, session
from types import SimpleNamespace
from datetime import datetime
from services.auth_service import *
from services.dashboard_service import *
import math
app = Flask(__name__)
app.secret_key = 'super_tajny_klucz'


def get_logged_in_user():
    if 'user_id' not in session:
        return None

    return SimpleNamespace(
        id=session['user_id'],
        username=session.get('username', 'J.SMITH'),
        role=session.get('role', 'ADMIN')
    )


@app.context_processor
def inject_current_user():
    return {
        'current_user': get_logged_in_user()
    }


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        logged_user = verify_user_login(username, password)

        if logged_user:
            session['user_id'] = logged_user['user_id']
            session['username'] = logged_user['username']
            session['role'] = logged_user['role']
            return redirect(url_for('dashboard'))

        return "Invalid username or password"

    return render_template('loginForm.html')


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username_exists(username):
            return "Username already exists"

        create_user(username, password)
        return redirect(url_for('login'))

    return render_template('regForm.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))



if __name__ == '__main__':
    app.run(debug=True)