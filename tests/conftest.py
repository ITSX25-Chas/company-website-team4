import pytest

from company_website import create_app
from company_website.config import Config


@pytest.fixture
def app(tmp_path, monkeypatch):
    # Egen databas per test, så att testerna inte rör data/ i repot och
    # inte påverkar varandra.
    monkeypatch.setattr(Config, 'DATABASE', str(tmp_path / 'database.db'))
    monkeypatch.setattr(Config, 'LEGACY_AUTH_DATABASE', str(tmp_path / 'legacy_auth.db'))
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()
