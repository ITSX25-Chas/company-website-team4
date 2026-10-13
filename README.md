# Company Website

A modular Flask application with Docker support.

## Local Development

Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Copy the environment file, set a random `SECRET_KEY` in it and run the app.
The app refuses to start without a key of at least 32 characters:

```bash
cp .env.example .env
python -c 'import secrets; print(secrets.token_hex(32))'   # paste into .env
python wsgi.py
```

Or with Flask CLI:

```bash
export PYTHONPATH=src
flask --app company_website run --port 7000
```

## Docker

Build and run with Docker Compose:

```bash
docker compose up --build
```

The SQLite database is persisted in a Docker volume (`app-data`).

In Kubernetes the key is read from the secret `company-website` (key
`secret-key`), which is created by hand and is not stored in git.

For Kubernetes (k3s), replace the Docker volume with a PersistentVolumeClaim pointing to `/app/data`.

## Tests

Run tests with pytest:

```bash
pytest
```

## Project Structure

```
.
├── src/
│   └── company_website/
│       ├── __init__.py
│       ├── app.py          # Flask app factory
│       ├── config.py       # Configuration
│       ├── db.py           # Database helpers & migrations
│       ├── models.py       # Data models
│       ├── auth.py         # Authentication blueprint
│       ├── routes.py       # Main blueprint
│       ├── migrations/
│       ├── templates/
│       └── static/
├── tests/
├── wsgi.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```
