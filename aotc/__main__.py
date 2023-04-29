import logging
import logging.config
import tomllib

import click

from ._logging import LOGGING
logging.config.dictConfig(LOGGING)

from .bandcamp import scrape as _scrape
from .config import Config

logger = logging.getLogger(__name__)


def _load_config() -> Config:
    with open("config.toml", "rb") as f:
        return Config(**tomllib.load(f))


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option('-u', '--url', required=True, type=str, help='URL to scrape')
def scrape(url: str) -> None:
    config = _load_config()
    logging.info("Running scrape command")
    releases = _scrape(url)
    for release in releases:
        print(release)


if __name__ == '__main__':
    cli()
