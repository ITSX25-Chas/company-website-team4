import pytest

from company_website import create_app
from company_website.config import Config


@pytest.mark.parametrize('key', [None, '', 'dev-secret-key'])
def test_app_refuses_to_start_without_a_proper_key(monkeypatch, key):
    monkeypatch.setattr(Config, 'SECRET_KEY', key)
    with pytest.raises(RuntimeError, match='SECRET_KEY'):
        create_app()


def test_app_uses_the_key_from_the_environment(app):
    assert app.config['SECRET_KEY'] == 'test-secret-key-only-used-by-the-tests'
