from flask import Flask, request, render_template, jsonify, redirect, url_for, session
from types import SimpleNamespace
from datetime import datetime
from services.auth_service import *
from services.dashboard_service import *
from services.transaction_service import *
from services.budget_service import *
from services.household_service import *
from services.auth_service import get_user_by_username
from services.category_service import add_category
import math
import re

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

        return render_template('loginForm.html', error="INVALID USERNAME OR PASSWORD")

    return render_template('loginForm.html')


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Regex Patterns
        username_pattern = r'^[a-zA-Z0-9_.-]{3,20}$'
        password_pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'

        # Validate Username
        if not re.match(username_pattern, username):
            return render_template('regForm.html', error="INVALID USERNAME: 3-20 characters, no spaces.")

        # Validate Password
        if not re.match(password_pattern, password):
            return render_template('regForm.html', error="WEAK PASSWORD: Min 8 chars, 1 upper, 1 lower, 1 number, 1 special.")

        # Check if username exists
        if username_exists(username):
            return render_template('regForm.html', error="USERNAME ALREADY TAKEN.")

        # Create user and redirect to login
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

    user_id = session['user_id']
    household_data = get_household_by_user(user_id)
    household_id = household_data['household_id'] if household_data else None

    if request.method == 'POST':
        amount = request.form['amount']
        budget_month = request.form['budget_month']
        budget_year = request.form['budget_year']
        category_id = request.form['category_id']
        scope = request.form['scope']

        add_budget(user_id, household_id, category_id, amount, budget_month, budget_year, scope)
        
        return redirect(url_for('dashboard'))

    
    # Fetch categories for the dropdown
    categories = get_user_categories(user_id, household_id)
    return render_template('add_budget.html', categories=categories)


# --- HOUSEHOLD ADMIN ROUTES ---

@app.route('/admin', methods=['GET'])
def admin():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    household = get_household_by_user(user_id)
    
    members = []
    current_user_status = None
    
    if household:
        members = get_household_members(household['household_id'])
        # Find current user's role to determine what UI to show
        for m in members:
            if m['user_id'] == user_id:
                current_user_status = m['user_status']
                break

    return render_template('household_admin.html', 
                           household=household, 
                           members=members,
                           current_user_status=current_user_status)


@app.route('/create_household', methods=['POST'])
def create_household_route():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    user_id = session['user_id']
    household_name = request.form['household_name']
    
    create_household(household_name, user_id)
    return redirect(url_for('admin'))


@app.route('/update_household', methods=['POST'])
def update_household():
    if 'user_id' not in session: return redirect(url_for('login'))
        
    user_id = session['user_id']
    new_name = request.form['household_name']
    
    household = get_household_by_user(user_id)
    if household:
        update_household_name(household['household_id'], new_name)
        
    return redirect(url_for('admin'))


@app.route('/add_member', methods=['POST'])
def add_member():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    user_id = session['user_id']
    target_username = request.form['username']
    
    household = get_household_by_user(user_id)
    if not household: return redirect(url_for('admin'))
    
    # Check if target user exists
    target_user = get_user_by_username(target_username)
    if target_user:
        # Add them as a standard member
        add_user_to_household(target_user[0], household['household_id'], 'member')
        
    return redirect(url_for('admin'))


@app.route('/grant_admin/<int:target_user_id>', methods=['GET'])
def grant_admin(target_user_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    update_user_household_role(target_user_id, 'admin')
    return redirect(url_for('admin'))


@app.route('/remove_member/<int:target_user_id>', methods=['GET'])
def remove_member(target_user_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    remove_user_from_household(target_user_id)
    return redirect(url_for('admin'))

@app.route('/add_category', methods=['GET', 'POST'])
def add_category_route():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        user_id = session['user_id']
        category_name = request.form['category_name']
        category_type = request.form['category_type']
        scope = request.form['scope']

        household_data = get_household_by_user(user_id)
        household_id = household_data['household_id'] if household_data else None

        add_category(user_id, household_id, category_name, category_type, scope)
        
        return redirect(url_for('dashboard'))

    return render_template('add_category.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    
    # Fetch household ID
    from services.household_service import get_household_by_user
    household_data = get_household_by_user(user_id)
    household_id = household_data['household_id'] if household_data else None

    # Get URL arguments
    scope = request.args.get('scope', 'individual')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    table_view = request.args.get('table_view', 'transactions')

    # --- MONTH FILTER LOGIC ---
    filter_month_str = request.args.get('filter_month')
    today = datetime.today()
    
    if filter_month_str:
        try:
            # HTML input type="month" returns YYYY-MM
            parsed_date = datetime.strptime(filter_month_str, '%Y-%m')
            target_year = parsed_date.year
            target_month = parsed_date.month
        except ValueError:
            target_year = today.year
            target_month = today.month
            filter_month_str = f"{today.year}-{today.month:02d}"
    else:
        target_year = today.year
        target_month = today.month
        filter_month_str = f"{today.year}-{today.month:02d}"

    # Scoped queries for charts and tables (now respecting month & year)
    summary = get_executive_summary(user_id, household_id, target_month, target_year, scope)
    expenditure_analysis = get_expenditure_analysis(user_id, household_id, target_month, target_year, scope)
    detailed_budgets = get_detailed_budgets(user_id, household_id, target_month, target_year, scope)

    # Chart logic
    max_spent = max([item['spent'] for item in expenditure_analysis], default=0)
    if max_spent == 0: y_axis_max = 100
    elif max_spent <= 100: y_axis_max = 100
    elif max_spent <= 500: y_axis_max = math.ceil(max_spent / 50) * 50
    elif max_spent <= 2000: y_axis_max = math.ceil(max_spent / 100) * 100
    else: y_axis_max = math.ceil(max_spent / 500) * 500
    
    y_axis_labels = [y_axis_max, y_axis_max * 0.75, y_axis_max * 0.50, y_axis_max * 0.25, 0]

    # Database Explorer logic
    explorer_data = []
    if table_view == 'transactions':
        explorer_data = get_transactions(user_id, start_date, end_date)
    elif table_view == 'budgets':
        from services.budget_service import filter_budgets
        explorer_data = filter_budgets(user_id)
    elif table_view == 'users':
        if household_data:
            from services.household_service import get_household_members
            explorer_data = get_household_members(household_data['household_id'])

    return render_template(
        'dashboard.html',
        total_budget=summary['total_budget'],
        total_spent=summary['total_spent'],
        total_remaining=summary['total_remaining'],
        detailed_budgets=detailed_budgets,
        explorer_data=explorer_data,
        expenditure_analysis=expenditure_analysis,
        y_axis_max=y_axis_max,
        y_axis_labels=y_axis_labels,
        selected_table_view=table_view,
        selected_start_date=start_date,
        selected_end_date=end_date,
        selected_scope=scope,           
        selected_filter_month=filter_month_str, # Passed to keep the input updated
        in_household=(household_id is not None) 
    )


if __name__ == '__main__':
    app.run(debug=True)