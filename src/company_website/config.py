import os


class Config:
    # Ingen reserv i koden: en nyckel som står i git kan alla använda för att
    # förfalska sessioner (F18). create_app vägrar starta utan nyckel.
    SECRET_KEY = os.environ.get('SECRET_KEY')
    # Webbläsaren skickar inte sessionscookien med POST från andra sajter.
    # Ett andra skydd utöver CSRF-token (F21).
    SESSION_COOKIE_SAMESITE = 'Lax'
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    DATABASE = os.path.join(BASE_DIR, 'data', 'database.db')
    LEGACY_AUTH_DATABASE = os.path.join(BASE_DIR, 'data', 'legacy_auth.db')
