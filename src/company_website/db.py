import glob
import os
import sqlite3

from .config import Config


def get_db():
    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(Config.DATABASE), exist_ok=True)
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    migration_dir = os.path.join(os.path.dirname(__file__), 'migrations')
    migration_files = sorted(glob.glob(os.path.join(migration_dir, '*.sql')))

    for filepath in migration_files:
        filename = os.path.basename(filepath)
        cursor.execute("SELECT 1 FROM schema_migrations WHERE version = ?", (filename,))
        if cursor.fetchone():
            continue

        with open(filepath, 'r') as f:
            cursor.executescript(f.read())

        cursor.execute("INSERT INTO schema_migrations (version) VALUES (?)", (filename,))
        conn.commit()

    conn.close()


def remove_legacy_db():
    # legacy_auth.db var en kopia av alla lösenordshashar för den gamla
    # inloggningen (F16, F20). Den används inte längre och ska inte ligga
    # kvar på volymen. Flera workers kan starta samtidigt, därav except.
    try:
        os.remove(Config.LEGACY_AUTH_DATABASE)
    except FileNotFoundError:
        pass
