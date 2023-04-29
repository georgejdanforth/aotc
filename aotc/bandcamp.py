import typing as t
from itertools import chain
from urllib.parse import ParseResult, urljoin, urlparse

import requests
from lxml import html

release_url_xpath = '//li[contains(@class, "music-grid-item")]/a/@href'
feature_url_xpath = '//li[contains(@class, "featured-item")]/a/@href'


def _is_valid_url(url: ParseResult) -> bool:
    try:
        return bool(url.scheme and url.netloc)
    except ValueError:
        return False


def _get_base_url(url: ParseResult) -> str:
    return f'{url.scheme}://{url.netloc}'


def _is_url_absolute(url: str) -> bool:
    return bool(urlparse(url).netloc)


def _get_release_urls(base_url: str, tree: html.Element) -> t.Generator[str, None, None]:
    for url in chain(tree.xpath(release_url_xpath), tree.xpath(feature_url_xpath)):
        if _is_url_absolute(url):
            yield url
        else:
            yield urljoin(base_url, url)


def scrape(url: str) -> None:
    parsed_url = urlparse(url)
    if not _is_valid_url(parsed_url):
        raise ValueError(f'Invalid URL: {url}')

    response = requests.get(url)
    if not response.ok:
        raise RuntimeError(f'Failed to fetch URL: {url}, status code: {response.status_code}')

    tree = html.fromstring(response.content)
    base_url = _get_base_url(parsed_url)
    release_urls = _get_release_urls(base_url, tree)
    print(list(release_urls))
