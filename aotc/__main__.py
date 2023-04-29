import logging
import logging.config

import click

from ._logging import LOGGING
logging.config.dictConfig(LOGGING)

from .bandcamp import scrape as _scrape

logger = logging.getLogger(__name__)


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option('-u', '--url', required=True, type=str, help='URL to scrape')
def scrape(url: str) -> None:
    logging.info("Running scrape command")
    releases = _scrape(url)
    for release in releases:
        print(release)


if __name__ == '__main__':
    cli()
