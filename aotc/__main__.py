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

logger = logging.getLogger(__name__)


class Context(t.NamedTuple):
    config: Config
    db: Database


def load_config() -> Config:
    with open('config.toml', 'rb') as f:
        return Config(**tomllib.load(f))


def inject_context(cmd: t.Callable) -> t.Callable:
    logger.info('Loading configuration')
    config = load_config()
    @wraps(cmd)
    def wrapper(*args: t.Any, **kwargs: t.Any) -> None:
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
    releases = _scrape(url)
    for release in releases:
        print(release)


@cli.command()
@click.option('-c', '--code', required=True, type=str, help='Spotify authorization code')
@inject_context
def authorize(ctx: Context, code: str) -> None:
    logging.info('Running authorize command')
    ctx.db.set_auth_code(code)


if __name__ == '__main__':
    logger.info('Starting up')
    cli()
