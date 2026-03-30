from flask import Flask, request, render_template, redirect, url_for
from flask_login import LoginManager, login_required, current_user, login_user, logout_user, UserMixin
from flask import Flask, request, render_template, jsonify
from db import get_connection
#request enable form handling
#render_template enable rendering html templates

app = Flask(__name__) #create flask app

app.secret_key = 'super_secret_key_for_development'

# Mock Database for testing
MOCK_USERS = {
    "admin": "password123",
    "jsmith": "budget2026"
}

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(user_id):
    if user_id in MOCK_USERS:
        return User(user_id)
    return None

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST']) 
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in MOCK_USERS and MOCK_USERS[username] == password:
            user = User(username)
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            error = "Invalid username or password. Please try again."
            
    return render_template('loginForm.html', error=error)

@app.route('/registration', methods=['GET', 'POST']) 
def registration():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        MOCK_USERS[username] = password
        
        return redirect(url_for('login'))
        
    return render_template('regForm.html')

@app.route('/dashboard')
@login_required 
def dashboard():
    return render_template('dashboard.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login')) 

if __name__ == '__main__':
    app.run(debug=True)
