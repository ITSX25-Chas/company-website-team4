from werkzeug.security import generate_password_hash

from company_website.db import get_db

PASSWORD = 'correct horse battery staple'


def set_password(username, password=PASSWORD, enabled=True):
    conn = get_db()
    conn.execute(
        "UPDATE users SET password_hash = ?, enabled = ? WHERE username = ?",
        (generate_password_hash(password), int(enabled), username),
    )
    conn.commit()
    conn.close()


def user_id(username):
    conn = get_db()
    row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return row['id']


def post(client, url, data=None):
    return client.post(url, data=data or {})


def login(client, username, password=PASSWORD):
    return post(client, '/login', {'username': username, 'password': password})


def logged_in_user(client):
    with client.session_transaction() as session:
        return session.get('_user_id')
