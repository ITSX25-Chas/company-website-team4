import re

import pytest

from tests.helpers import login, set_password, user_id


@pytest.fixture
def alice(client):
    set_password('alice')
    login(client, 'alice')
    return client


def pages(client):
    return ['/', '/employees', f"/profiles/{user_id('alice')}", f"/profiles/{user_id('alice')}/edit"]


def test_headers_on_every_page(alice):
    for url in pages(alice) + ['/login', '/healthz', '/static/js/base.js']:
        headers = alice.get(url).headers
        csp = headers['Content-Security-Policy']
        assert "script-src 'self'" in csp, url
        assert "frame-ancestors 'none'" in csp, url
        assert headers['X-Frame-Options'] == 'DENY', url
        assert headers['X-Content-Type-Options'] == 'nosniff', url


def test_csp_does_not_allow_inline_scripts(client):
    csp = client.get('/').headers['Content-Security-Policy']
    script_src = re.search(r"script-src ([^;]*)", csp).group(1)
    assert 'unsafe-inline' not in script_src


def test_pages_have_no_inline_scripts(alice):
    # Med script-src 'self' skulle ett inline-skript blockeras och sidan sluta fungera.
    for url in pages(alice) + ['/login']:
        html = alice.get(url).get_data(as_text=True)
        assert not re.search(r'<script(?![^>]*\bsrc=)[^>]*>', html), url
        assert not re.search(r'\son[a-z]+=', html), url
