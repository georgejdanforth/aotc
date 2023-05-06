import logging
import logging.config
import tomllib
import typing as t
from functools import wraps

import click
import psycopg

from ._logging import LOGGING
logging.config.dictConfig(LOGGING)

from .bandcamp import scrape as _scrape
from .config import Config
from .database import Database
from .spotify import SpotifyClient

logger = logging.getLogger(__name__)


class Context(t.NamedTuple):
    config: Config
    db: Database


def load_config() -> Config:
    with open('config.toml', 'rb') as f:
        return Config(**tomllib.load(f))


def inject_context(cmd: t.Callable) -> t.Callable:
    @wraps(cmd)
    def wrapper(*args: t.Any, **kwargs: t.Any) -> None:
        logger.info('Loading configuration')
        config = load_config()
        logger.info('Connecting to database')
        with psycopg.connect(config.database.connection_string) as connection:
            logger.info('Connected to database')
            ctx = Context(config=config, db=Database(connection))
            cmd(ctx, *args, **kwargs)

    return wrapper


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option('-u', '--url', required=True, type=str, help='URL to scrape')
@inject_context
def scrape(ctx: Context, url: str) -> None:
    logging.info('Running scrape command')
    refresh_token = ctx.db.get_refresh_token()
    spotify = SpotifyClient(ctx.config.spotify, refresh_token)
    releases = _scrape(url)
    for release in releases:
        spotify.search(release)


@cli.command()
@inject_context
def authorize(ctx: Context) -> None:
    logging.info('Running authorize command')

    client = SpotifyClient(ctx.config.spotify)
    auth_url = client.auth_redirect_url

    print(f"""Visit the following URL to authorize the application:

    {auth_url}

After being redirected, copy the authorization code from the URL and enter it below.
""")

    code = input('Authorization code: ').strip()

    refresh_token = client.authorize(code)
    ctx.db.set_refresh_token(refresh_token)


if __name__ == '__main__':
    cli()
