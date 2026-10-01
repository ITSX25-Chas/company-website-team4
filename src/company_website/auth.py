from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db
from .models import User

auth_bp = Blueprint('auth', __name__)

login_manager = LoginManager()

# Kontrolleras när användarnamnet inte finns, så att det svaret tar lika lång
# tid som ett felaktigt lösenord. Annars avslöjar svarstiden vilka konton som
# finns (F58).
DUMMY_PASSWORD_HASH = generate_password_hash('not-a-real-password')


@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return User(
            str(row['id']),
            row['username'],
            row['password_hash'],
            row['first_name'],
            row['last_name'],
            row['email'],
            row['about'],
            row['role'],
            row['internal_notes'],
            row['email_signature'],
        )
    return None


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET' and current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()

        # Lösenordet verifieras alltid mot hashen, aldrig jämförs med den
        # (F16, F20). Ett värde som inte är en hash, t.ex. ett lösenord i
        # klartext, ger False.
        password_hash = row['password_hash'] if row else DUMMY_PASSWORD_HASH
        if not check_password_hash(password_hash, password):
            row = None

        if row and not row['enabled']:
            row = None

        if row:
            user = User(
                str(row['id']),
                row['username'],
                row['password_hash'],
                row['first_name'],
                row['last_name'],
                row['email'],
                row['about'],
                row['role'],
                row['internal_notes'],
                row['email_signature'],
            )
            login_user(user)
            flash('Login successful!', 'success')
            return render_template('login.html', user=user)
        flash('Invalid username or password.', 'error')
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.index'))
