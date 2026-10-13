import re

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


def csrf_token(client):
    # Varje sida har ett formulär med token: inloggningen eller utloggningen.
    html = client.get('/').get_data(as_text=True)
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def post(client, url, data=None):
    data = dict(data or {})
    data['csrf_token'] = csrf_token(client)
    return client.post(url, data=data)


def login(client, username, password=PASSWORD):
    return post(client, '/login', {'username': username, 'password': password})


def logged_in_user(client):
    with client.session_transaction() as session:
        return session.get('_user_id')
