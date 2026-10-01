import importlib

import pytest


@pytest.fixture
def wsgi(app):
    # Importeras efter app-fixturen, så att create_app i wsgi.py använder
    # testets tillfälliga databas.
    return importlib.import_module('wsgi')


def test_debug_is_off_when_not_set(wsgi, monkeypatch):
    monkeypatch.delenv('FLASK_DEBUG', raising=False)
    assert wsgi.debug_enabled() is False


@pytest.mark.parametrize('value, expected', [
    ('true', True), ('1', True), ('false', False), ('0', False), ('', False), ('nonsense', False),
])
def test_debug_only_on_when_explicitly_enabled(wsgi, monkeypatch, value, expected):
    monkeypatch.setenv('FLASK_DEBUG', value)
    assert wsgi.debug_enabled() is expected
