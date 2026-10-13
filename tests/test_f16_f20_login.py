import os

from company_website import auth, create_app
from company_website.config import Config
from company_website.db import get_db

from tests.helpers import PASSWORD, logged_in_user, login, set_password, user_id


def test_correct_password_logs_in(client):
    set_password('dev')
    login(client, 'dev')
    assert logged_in_user(client) == str(user_id('dev'))


def test_wrong_password_is_rejected(client):
    set_password('dev')
    login(client, 'dev', 'wrong')
    assert logged_in_user(client) is None


def test_sql_injection_does_not_bypass_login(client):
    set_password('dev')
    response = login(client, "' OR username = 'dev' --", 'x')
    assert logged_in_user(client) is None
    assert b'Invalid username or password.' in response.data


def test_stored_hash_is_not_accepted_as_password(client):
    # Seed-hashen, alltså samma värde som den gamla legacy_auth.db hade.
    conn = get_db()
    stored_hash = conn.execute("SELECT password_hash FROM users WHERE username = 'dev'").fetchone()[0]
    conn.close()

    login(client, 'dev', stored_hash)
    assert logged_in_user(client) is None


def test_plaintext_value_in_hash_column_is_not_accepted(client):
    # Seed-kontot flag hade sitt lösenord i klartext i password_hash.
    conn = get_db()
    conn.execute("UPDATE users SET password_hash = 'plaintext', enabled = 1 WHERE username = 'dev'")
    conn.commit()
    conn.close()

    login(client, 'dev', 'plaintext')
    assert logged_in_user(client) is None


def test_disabled_account_cannot_log_in(client):
    set_password('alice', enabled=False)
    login(client, 'alice')
    assert logged_in_user(client) is None


def test_unknown_username_still_checks_a_hash(client, monkeypatch):
    calls = []
    real_check = auth.check_password_hash
    monkeypatch.setattr(auth, 'check_password_hash',
                        lambda h, p: calls.append(h) or real_check(h, p))

    login(client, 'no-such-user', PASSWORD)

    assert calls == [auth.DUMMY_PASSWORD_HASH]


def test_legacy_database_is_removed_on_startup(app):
    with open(Config.LEGACY_AUTH_DATABASE, 'w') as f:
        f.write('old copy of all password hashes')

    create_app()

    assert not os.path.exists(Config.LEGACY_AUTH_DATABASE)
