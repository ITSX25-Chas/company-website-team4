from company_website.db import get_db

from tests.helpers import login, post, set_password, user_id


def profile_row(username):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return row


def test_other_users_edit_form_is_forbidden(client):
    set_password('alice')
    login(client, 'alice')

    response = client.get(f"/profiles/{user_id('dev')}/edit")

    assert response.status_code == 403
    assert b'staging123' not in response.data


def test_other_users_profile_cannot_be_changed(client):
    set_password('alice')
    login(client, 'alice')
    before = dict(profile_row('dev'))

    response = post(client, f"/profiles/{user_id('dev')}/edit",
                    {'first_name': 'Hacked', 'email_signature': 'pwned'})

    assert response.status_code == 403
    assert dict(profile_row('dev')) == before


def test_own_profile_can_be_edited(client):
    set_password('alice')
    login(client, 'alice')

    assert client.get(f"/profiles/{user_id('alice')}/edit").status_code == 200
    response = post(client, f"/profiles/{user_id('alice')}/edit", {'first_name': 'Alicia'})

    assert response.status_code == 302
    assert profile_row('alice')['first_name'] == 'Alicia'
