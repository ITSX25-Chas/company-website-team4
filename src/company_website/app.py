from flask import Flask

from .config import Config
from .db import init_db, remove_legacy_db
from .auth import auth_bp, login_manager
from .routes import main_bp

MIN_SECRET_KEY_LENGTH = 32


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    if len(app.config.get('SECRET_KEY') or '') < MIN_SECRET_KEY_LENGTH:
        raise RuntimeError(
            f'SECRET_KEY must be set to a random value of at least '
            f'{MIN_SECRET_KEY_LENGTH} characters'
        )

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'error'

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    init_db()
    remove_legacy_db()

    return app
