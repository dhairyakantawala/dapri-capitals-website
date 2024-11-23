from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key'


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@app.route('/')
def welcome():
    return render_template('welcome.html')



# Load users from 'data/users.json' file
def load_users():
    if os.path.exists('data/users.json'):
        with open('data/users.json', 'r') as file:
            return json.load(file)
    return {}

# Save users to 'data/users.json' file
def save_users(users):
    with open('data/users.json', 'w') as file:
        json.dump(users, file)

class User(UserMixin):
    def __init__(self, id, username, password_hash, access):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.access = access

    def is_authenticated(self):
        return True  # By default, we're assuming the user is authenticated if they exist.

@login_manager.user_loader
def load_user(user_id):
    users = load_users()
    user_data = users.get(user_id)
    
    if user_data:
        return User(user_id, user_id, user_data['password_hash'], user_data['access'])
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        users = load_users()
        user = users.get(username)
        
        if user and check_password_hash(user['password_hash'], password):
            user_obj = User(username, username, user['password_hash'], user['access'])
            login_user(user_obj)
            return redirect(url_for('admin' if user_obj.username == 'admin' else 'user'))
        
        flash('Invalid credentials', 'danger')
    
    return render_template('login.html')

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if current_user.username != 'admin':
        return redirect(url_for('login'))
    
    users = load_users()
    if request.method == 'POST':
        new_username = request.form['new_username']
        new_password = request.form['new_password']
        new_access = request.form.getlist('notebook_access')
        
        if new_username in users:
            flash('User already exists!', 'danger')
        else:
            password_hash = generate_password_hash(new_password)
            users[new_username] = {
                'password_hash': password_hash,
                'access': new_access
            }
            save_users(users)
            flash(f'User {new_username} added successfully!', 'success')
    
    notebooks = os.listdir('volia')
    return render_template('admin.html', users=users, notebooks=notebooks)

@app.route('/user')
@login_required
def user():
    if current_user.username == 'admin':
        return redirect(url_for('admin'))
    
    users = load_users()
    user_access = users[current_user.username]['access']
    accessible_notebooks = [notebook for notebook in os.listdir('volia') if notebook in user_access]
    
    return render_template('user.html', notebooks=accessible_notebooks)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('register.html')



if __name__ == '__main__':
    app.run(debug=True)
