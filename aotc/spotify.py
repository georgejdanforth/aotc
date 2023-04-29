from datetime import datetime
from urllib.parse import quote_plus

import requests

# from .bandcamp import Release
from .config import SpotifyConfig


class _SpotifyClient:
    def __init__(self, config: SpotifyConfig) -> None:
        self._config = config
        self._session = requests.Session()

        self._authorization_code: str | None = None
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._token_type: str | None = None
        self._expires_in: datetime | None = None

    @property
    def encoded_redirect_uri(self) -> str:
        return quote_plus(self._config.redirect_uri)

    @property
    def auth_redirect_url(self):
        return (
            f'https://accounts.spotify.com/authorize/'
            f'?client_id={self._config.client_id}'
            f'&response_type=code'
            f'&redirect_uri={self.encoded_redirect_uri}'
            f'&scope=playlist-modify-public'
        )


def get_auth_url(config: SpotifyConfig) -> str:
    return _SpotifyClient(config).auth_redirect_url
