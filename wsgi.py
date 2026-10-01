import os

from dotenv import load_dotenv

# Läser .env vid lokal körning (python wsgi.py). I imagen finns ingen .env,
# och värden som redan finns i miljön skrivs inte över.
load_dotenv()

from company_website import create_app  # noqa: E402

app = create_app()


def debug_enabled():
    # Av som standard. Debuggern kan köra Python-kod åt den som når sidan,
    # så den ska bara slås på uttryckligen, t.ex. i en lokal .env (F60).
    return os.environ.get('FLASK_DEBUG', 'false').lower() in ('1', 'true', 'yes')


if __name__ == "__main__":
    app.run(debug=debug_enabled(), port=7000)
