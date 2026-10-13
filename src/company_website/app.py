from flask import Flask
from flask_wtf.csrf import CSRFProtect

from .cli import set_password_command
from .config import Config
from .db import init_db, remove_legacy_db
from .auth import auth_bp, login_manager
from .routes import main_bp

MIN_SECRET_KEY_LENGTH = 32

# Alla POST kräver en CSRF-token, i formulärfältet csrf_token eller i
# headern X-CSRFToken (F21).
csrf = CSRFProtect()

# Skickas med varje svar (F61). CSP:n tillåter bara skript från appen själv,
# så att injicerad HTML inte kan köra skript. Inline-stilar finns kvar i
# mallarna och tillåts därför. frame-ancestors och X-Frame-Options hindrar
# att sidan ramas in av en annan sajt (clickjacking).
SECURITY_HEADERS = {
    'Content-Security-Policy': (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
    ),
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'Referrer-Policy': 'same-origin',
}


def add_security_headers(response):
    for name, value in SECURITY_HEADERS.items():
        response.headers.setdefault(name, value)
    return response


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    if len(app.config.get('SECRET_KEY') or '') < MIN_SECRET_KEY_LENGTH:
        raise RuntimeError(
            f'SECRET_KEY must be set to a random value of at least '
            f'{MIN_SECRET_KEY_LENGTH} characters'
        )

    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'error'

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.cli.add_command(set_password_command)
    app.after_request(add_security_headers)

    init_db()
    remove_legacy_db()

    return app
