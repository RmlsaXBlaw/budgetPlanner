from flask import Flask, request, render_template, jsonify, redirect, url_for, session
from types import SimpleNamespace
from datetime import datetime
from services.auth_service import *
from services.dashboard_service import *
import math
app = Flask(__name__)
app.secret_key = 'klucz'


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


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    table_view = request.args.get('table_view', 'transactions')

    summary = get_executive_summary(user_id)
    detailed_budgets = get_detailed_budgets(user_id)

    # do wykresow 
    today = datetime.today()
    expenditure_analysis = get_expenditure_analysis(user_id, today.month, today.year)
    max_spent = max([item['spent'] for item in expenditure_analysis], default=0)

    if max_spent == 0:
        y_axis_max = 100
    elif max_spent <= 100:
        y_axis_max = 100
    elif max_spent <= 500:
        y_axis_max = math.ceil(max_spent / 50) * 50
    elif max_spent <= 2000:
        y_axis_max = math.ceil(max_spent / 100) * 100
    else:
        y_axis_max = math.ceil(max_spent / 500) * 500
    y_axis_labels = [
        y_axis_max,
        y_axis_max * 0.75,
        y_axis_max * 0.50,
        y_axis_max * 0.25,
        0
    ]

    explorer_data = []
    if table_view == 'transactions':
        explorer_data = get_transactions(user_id, start_date, end_date)

    return render_template(
        'dashboard.html',
        total_budget=summary['total_budget'], #calkowity budzet
        total_spent=summary['total_spent'], # suma wydatkow
        total_remaining=summary['total_remaining'], # pozostala kwota
        detailed_budgets=detailed_budgets, # tabela z budzetami i wydatkami
        explorer_data=explorer_data, # dane do eksploratora
        expenditure_analysis=expenditure_analysis, # dane do wykresu
        y_axis_max=y_axis_max, # maksymalna wartosc na osi Y 
        y_axis_labels=y_axis_labels, # etykiety osi Y
        selected_table_view=table_view, # wybrany widok tabeli
        selected_start_date=start_date, # filtr - data od 
        selected_end_date=end_date # filtr - data do 
    )


if __name__ == '__main__':
    app.run(debug=True)