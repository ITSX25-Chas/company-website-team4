import click
from werkzeug.security import generate_password_hash

from .db import get_db

MIN_PASSWORD_LENGTH = 12


@click.command('set-password')
@click.argument('username')
def set_password_command(username):
    """Sätter ett nytt lösenord för USERNAME.

    Lösenordet läses från terminalen och inte från kommandoraden, så att det
    inte syns i processlistan eller i Falcos larm (F33). Används för att
    rotera lösenord vars hashar ligger i git-historiken (F22).
    """
    password = click.prompt('New password', hide_input=True, confirmation_prompt=True)
    if len(password) < MIN_PASSWORD_LENGTH:
        raise click.ClickException(f'Password must be at least {MIN_PASSWORD_LENGTH} characters')

    conn = get_db()
    cursor = conn.execute(
        "UPDATE users SET password_hash = ? WHERE username = ?",
        (generate_password_hash(password), username),
    )
    conn.commit()
    conn.close()
    if cursor.rowcount == 0:
        raise click.ClickException(f'No user named {username}')
    click.echo(f'Password updated for {username}')
