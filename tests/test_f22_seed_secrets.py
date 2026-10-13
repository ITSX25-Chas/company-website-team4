from werkzeug.security import check_password_hash

from company_website.db import get_db


def all_rows():
    conn = get_db()
    rows = [dict(r) for r in conn.execute("SELECT * FROM users")]
    conn.close()
    return rows


def test_flag_test_account_is_removed(app):
    assert 'flag' not in [r['username'] for r in all_rows()]


def test_no_credentials_or_flags_left_in_user_data(app):
    text = repr(all_rows())
    assert 'staging123' not in text
    assert 'ITSX25{' not in text


def test_set_password_reads_password_from_prompt(app):
    result = app.test_cli_runner().invoke(
        args=['set-password', 'dev'], input='a-brand-new-password\na-brand-new-password\n')

    assert result.exit_code == 0, result.output
    stored = next(r for r in all_rows() if r['username'] == 'dev')['password_hash']
    assert check_password_hash(stored, 'a-brand-new-password')


def test_set_password_rejects_short_passwords(app):
    result = app.test_cli_runner().invoke(args=['set-password', 'dev'], input='short\nshort\n')
    assert result.exit_code != 0
    assert 'at least 12' in result.output


def test_set_password_fails_for_unknown_user(app):
    result = app.test_cli_runner().invoke(
        args=['set-password', 'nobody'], input='a-brand-new-password\na-brand-new-password\n')
    assert result.exit_code != 0
    assert 'No user named nobody' in result.output
