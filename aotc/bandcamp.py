import re
import typing as t
from datetime import date, datetime
from dataclasses import dataclass
from itertools import chain
from urllib.parse import ParseResult, urljoin, urlparse

import requests
from lxml import html

_feature_url_xpath = '//li[contains(@class, "featured-item")]/a/@href'
_release_url_xpath = '//li[contains(@class, "music-grid-item")]/a/@href'
_release_title_xpath = '//div[@id="name-section"]/h2/text()'
_release_artist_xpath = '//div[@id="name-section"]/h3/span/a/text()'
_release_date_xpath = '//div[@class="tralbumData tralbum-credits"]/text()'

_re_release_date = re.compile(r'^released (\w+ \d{1,2}, \d{4})$')


@dataclass
class Release:
    url: str
    artist: str
    title: str
    date: t.Optional[date]


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
    for url in chain(tree.xpath(_release_url_xpath), tree.xpath(_feature_url_xpath)):
        if _is_url_absolute(url):
            yield url
        else:
            yield urljoin(base_url, url)


def _get_text(tree: html.Element, xpath: str) -> str:
    return tree.xpath(xpath)[0].strip()


def _get_release_date(tree: html.Element) -> t.Optional[date]:
    text_elements = tree.xpath(_release_date_xpath)
    if not text_elements:
        return None

    for text_element in text_elements:
        match = _re_release_date.match(text_element.strip())
        if match:
            return datetime.strptime(match.group(1), "%B %d, %Y").date()


def _scrape_release_urls(url: str) -> t.Generator[str, None, None]:
    parsed_url = urlparse(url)
    if not _is_valid_url(parsed_url):
        raise ValueError(f'Invalid URL: {url}')

    response = requests.get(url)
    if not response.ok:
        raise RuntimeError(f'Failed to fetch URL: {url}, status code: {response.status_code}')

    tree = html.fromstring(response.content)
    base_url = _get_base_url(parsed_url)
    release_urls = _get_release_urls(base_url, tree)
    yield from release_urls


def _scrape_release(url: str) -> Release:
    response = requests.get(url)
    if not response.ok:
        raise RuntimeError(f'Failed to fetch release URL: {url}, status code: {response.status_code}')

    tree = html.fromstring(response.content)

    title = _get_text(tree, _release_title_xpath)
    artist = _get_text(tree, _release_artist_xpath)
    release_date = _get_release_date(tree)

    return Release(url, artist, title, release_date)


def scrape(url: str) -> None:
    release_urls = _scrape_release_urls(url)
    for release_url in release_urls:
        release = _scrape_release(release_url)
        print(release)
