import re

from flask import Blueprint, jsonify, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from .db import get_db
from .models import User

main_bp = Blueprint('main', __name__)
COMPANY_NAME = 'Placeholder Industries'
EMAIL_PREVIEW_MAX_LENGTH = 200
# Signaturen är text med platshållare, inte en Jinja-mall. Bara {{ namn }}
# med ett av de tillåtna namnen byts ut, allt annat lämnas orört. Användarens
# text får aldrig renderas som mall, eftersom den då körs på servern (F17).
EMAIL_VARIABLE_PATTERN = re.compile(r"{{\s*(\w+)\s*}}")


def _render_email_preview(template, user):
    values = {
        'firstname': user.first_name or '',
        'lastname': user.last_name or '',
        'email': user.email or '',
        'role': user.role or '',
        'company': COMPANY_NAME,
    }
    return EMAIL_VARIABLE_PATTERN.sub(
        lambda match: values.get(match.group(1), match.group(0)), template
    )


@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('home.html')
    return render_template('index.html')


@main_bp.route('/profile')
@login_required
def profile():
    return redirect(url_for('main.view_profile', id=current_user.id))


@main_bp.route('/profiles/<int:id>')
@login_required
def view_profile(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return "User not found", 404
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
    return render_template('view_profile.html', user=user)


@main_bp.route('/profiles/<int:id>/email-preview', methods=['POST'])
@login_required
def email_preview(id):
    if str(current_user.id) != str(id):
        return "Forbidden", 403

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return "User not found", 404

    user = User(
        str(row['id']), row['username'], row['password_hash'], row['first_name'],
        row['last_name'], row['email'], row['about'], row['role'], row['internal_notes']
    )
    email_template = request.form.get('email_template', '')
    if len(email_template) > EMAIL_PREVIEW_MAX_LENGTH:
        return "Email template is too long", 400

    return jsonify(preview=_render_email_preview(email_template, user))


@main_bp.route('/profiles/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_profile(id):
    # Bara ägaren får se och ändra sin profil. Formuläret visar även
    # internal_notes, som inte ska synas för andra (F19).
    if str(current_user.id) != str(id):
        return "Forbidden", 403

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return "User not found", 404

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

    if request.method == 'POST':
        first_name = request.form.get('first_name', '')
        last_name = request.form.get('last_name', '')
        email = request.form.get('email', '')
        about = request.form.get('about', '')
        role = request.form.get('role', '')
        internal_notes = request.form.get('internal_notes', '')
        email_signature = request.form.get('email_signature', user.email_signature)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users
            SET first_name = ?, last_name = ?, email = ?, about = ?, role = ?, internal_notes = ?,
                email_signature = ?
            WHERE id = ?
        ''', (first_name, last_name, email, about, role, internal_notes, email_signature, id))
        conn.commit()
        conn.close()

        flash('Profile updated!', 'success')
        return redirect(url_for('main.view_profile', id=id))

    return render_template('edit_profile.html', user=user)


@main_bp.route('/employees')
@login_required
def employees():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, first_name, last_name, role FROM users")
    rows = cursor.fetchall()
    conn.close()
    employees_list = []
    for row in rows:
        employees_list.append({
            'id': row['id'],
            'username': row['username'],
            'name': f"{row['first_name'] or ''} {row['last_name'] or ''}".strip(),
            'role': row['role']
        })
    return render_template('employees.html', employees=employees_list)


@main_bp.route('/healthz')
def health():
    status = {"status": "healthy"}
    code = 200
    try:
        db = get_db()
        db.execute("SELECT 1")
        status["db"] = "connected"
    except Exception:
        status["status"] = "unhealthy"
        status["db"] = "disconnected"
        code = 503
    return jsonify(status), code
