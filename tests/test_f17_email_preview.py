import pytest

from company_website.models import User
from company_website.routes import _render_email_preview

from tests.helpers import login, post, set_password, user_id


def preview(template):
    user = User('1', 'sample', '', first_name='Ada', role='Engineer')
    return _render_email_preview(template, user)


@pytest.mark.parametrize('template', [
    '{{ 7 * 7 }}',
    '{{ config }}',
    '{{ email.__class__ }}',
    '{{ cycler.__init__.__globals__.os }}',
    '{% for x in range(3) %}x{% endfor %}',
    '{{ firstname|upper }}',
])
def test_template_syntax_is_not_evaluated(template):
    assert preview(template) == template


def test_only_known_variables_are_replaced():
    assert preview('{{firstname}} / {{ role }} / {{ unknown }}') == 'Ada / Engineer / {{ unknown }}'


def test_values_are_inserted_as_text_not_as_template():
    user = User('1', 'sample', '', first_name='{{ 7 * 7 }}')
    assert _render_email_preview('{{ firstname }}', user) == '{{ 7 * 7 }}'


def test_preview_endpoint_does_not_leak_config(app, client):
    set_password('dev')
    login(client, 'dev')

    response = post(client, f"/profiles/{user_id('dev')}/email-preview",
                    {'email_template': '{{ config }} {{ 7 * 7 }} {{ firstname }}'})

    assert response.status_code == 200
    assert response.get_json()['preview'] == '{{ config }} {{ 7 * 7 }} Questionable'
    assert app.config['SECRET_KEY'] not in response.get_data(as_text=True)
