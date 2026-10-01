from dotenv import load_dotenv

# Läser .env vid lokal körning (python wsgi.py). I imagen finns ingen .env,
# och värden som redan finns i miljön skrivs inte över.
load_dotenv()

from company_website import create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    import os
    debug_mode = os.environ.get('FLASK_DEBUG', 'true').lower() not in ('0', 'false', 'no')
    app.run(debug=debug_mode, port=7000)
