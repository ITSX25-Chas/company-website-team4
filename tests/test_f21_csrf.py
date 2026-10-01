import pytest

from tests.helpers import PASSWORD, csrf_token, logged_in_user, login, post, set_password, user_id


@pytest.fixture
def alice(client):
    set_password('alice')
    login(client, 'alice')
    assert logged_in_user(client) == str(user_id('alice'))
    return client


def test_login_without_token_is_rejected(client):
    set_password('alice')
    response = client.post('/login', data={'username': 'alice', 'password': PASSWORD})
    assert response.status_code == 400
    assert logged_in_user(client) is None


def test_profile_edit_without_token_is_rejected(alice):
    response = alice.post(f"/profiles/{user_id('alice')}/edit", data={'first_name': 'Forged'})
    assert response.status_code == 400


def test_email_preview_without_token_is_rejected(alice):
    response = alice.post(f"/profiles/{user_id('alice')}/email-preview",
                          data={'email_template': 'x'})
    assert response.status_code == 400


def test_token_from_another_session_is_rejected(app, alice):
    other_token = csrf_token(app.test_client())
    response = alice.post(f"/profiles/{user_id('alice')}/edit",
                          data={'first_name': 'Forged', 'csrf_token': other_token})
    assert response.status_code == 400


def test_logout_requires_post_with_token(alice):
    assert alice.get('/logout').status_code == 405
    assert alice.post('/logout').status_code == 400
    assert logged_in_user(alice) is not None

    post(alice, '/logout')
    assert logged_in_user(alice) is None


def test_session_cookie_is_samesite_lax(client):
    set_password('alice')
    response = login(client, 'alice')
    cookie = next(h for h in response.headers.getlist('Set-Cookie') if h.startswith('session='))
    assert 'SameSite=Lax' in cookie
    assert 'HttpOnly' in cookie
