from flask import Flask, request, render_template, jsonify, redirect, url_for, session
from types import SimpleNamespace
from datetime import datetime
from services.auth_service import *
from services.dashboard_service import *
from services.transaction_service import *
from services.budget_service import *
from services.household_service import *
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

@app.route('/add_transaction', methods=['GET', 'POST'])
def add_transaction_route():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    household_data = get_household_by_user(user_id)
    household_id = household_data['household_id'] if household_data else None

    if request.method == 'POST':
        amount = request.form['amount']
        transaction_date = request.form['transaction_date']
        category_id = request.form['category_id']
        transaction_desc = request.form.get('transaction_desc', None)

        add_transaction(user_id, household_id, category_id, amount, transaction_date, transaction_desc)
        return redirect(url_for('dashboard'))

    # Fetch categories for the GET request (loading the form)
    categories = get_user_categories(user_id, household_id)
    return render_template('add_transaction.html', categories=categories)

@app.route('/add_budget', methods=['GET', 'POST'])
def add_budget_route():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        user_id = session['user_id']
        amount = request.form['amount']
        budget_month = request.form['budget_month']
        budget_year = request.form['budget_year']
        category_id = request.form['category_id']
        scope = request.form['scope']

        household_data = get_household_by_user(user_id)
        household_id = household_data['household_id'] if household_data else None

        add_budget(user_id, household_id, category_id, amount, budget_month, budget_year, scope)
        
        return redirect(url_for('dashboard'))

    return render_template('add_budget.html')


# --- HOUSEHOLD ADMIN ROUTES ---

@app.route('/admin', methods=['GET'])
def admin():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    household = get_household_by_user(user_id)
    
    members = []
    if household:
        members = get_household_members(household['household_id'])

    return render_template('household_admin.html', household=household, members=members)


@app.route('/update_household', methods=['POST'])
def update_household():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    new_name = request.form['household_name']
    
    household = get_household_by_user(user_id)
    if household:
        update_household_name(household['household_id'], new_name)
        
    return redirect(url_for('admin'))


@app.route('/remove_member/<int:target_user_id>', methods=['GET'])
def remove_member(target_user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    # In a real app, you'd want to check if the current user has 'admin' status 
    # for this household before allowing them to remove someone.
    remove_user_from_household(target_user_id)
    
    return redirect(url_for('admin'))

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