import click

from .bandcamp import scrape as _scrape


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option('-u', '--url', required=True, type=str, help='URL to scrape')
def scrape(url: str) -> None:
    _scrape(url)


if __name__ == '__main__':
    cli()
