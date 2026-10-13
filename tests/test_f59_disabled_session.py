from company_website.db import get_db

from tests.helpers import logged_in_user, login, set_password, user_id


def test_disabling_an_account_ends_its_session(client):
    set_password('alice')
    login(client, 'alice')
    assert client.get('/employees').status_code == 200

    conn = get_db()
    conn.execute("UPDATE users SET enabled = 0 WHERE username = 'alice'")
    conn.commit()
    conn.close()

    response = client.get('/employees')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_enabled_account_keeps_its_session(client):
    set_password('alice')
    login(client, 'alice')
    assert logged_in_user(client) == str(user_id('alice'))
    assert client.get('/employees').status_code == 200
