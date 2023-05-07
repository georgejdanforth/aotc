import logging
import typing as t
from base64 import b64encode
from datetime import datetime, timedelta
from functools import wraps
from urllib.parse import quote, quote_plus

import requests

from .bandcamp import Release
from .config import SpotifyConfig

logger = logging.getLogger(__name__)


_token_url = 'https://accounts.spotify.com/api/token'
_search_url = 'https://api.spotify.com/v1/search'
_album_tracks_url = 'https://api.spotify.com/v1/albums/{album_id}/tracks'
_playlist_add_url = 'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'


class BadResponseException(Exception):
    def __init__(self, message: str, response: requests.Response) -> None:
        self.message = message
        self.response = response

    def __str__(self) -> str:
        return f'{self.message}: {self.response.status_code} {self.response.json()}'



def require_access_token(method: t.Callable) -> t.Callable:
    @wraps(method)
    def wrapper(self: 'SpotifyClient', *args: t.Any, **kwargs: t.Any) -> t.Any:
        if self._refresh_token is None:
            raise RuntimeError('Need refresh token to authenticate')

        now = datetime.utcnow()
        if self._access_token is None or self._expires_at is None or now > self._expires_at:
            self._get_access_token()

        return method(self, *args, **kwargs)

    return wrapper


class SpotifyClient:
    def __init__(self, config: SpotifyConfig, refresh_token: str | None = None) -> None:
        self._config = config
        self._session = requests.Session()

        self._refresh_token = refresh_token

        self._access_token: str | None = None
        self._expires_at: datetime | None = None

    @property
    def _auth_header(self) -> str:
        return 'Basic ' + b64encode(
            f'{self._config.client_id}:{self._config.client_secret}'.encode('utf-8')
        ).decode('utf-8')

    @property
    def _encoded_redirect_uri(self) -> str:
        return quote_plus(self._config.redirect_uri)

    @property
    def auth_redirect_url(self) -> str:
        return (
            f'https://accounts.spotify.com/authorize/'
            f'?client_id={self._config.client_id}'
            f'&response_type=code'
            f'&redirect_uri={self._encoded_redirect_uri}'
            f'&scope=playlist-modify-public'
        )

    def authorize(self, authorization_code: str) -> str:
        headers = {
            'Authorization': self._auth_header,
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        params = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': self._config.redirect_uri,
        }

        response = self._session.post(_token_url, headers=headers, params=params)
        if not response.ok:
            raise BadResponseException('Failed to authorize with Spotify', response)

        data = response.json()

        return data['refresh_token']


    def _get_access_token(self) -> None:
        if not self._refresh_token:
            raise RuntimeError('No refresh token')

        headers = {
            'Authorization': self._auth_header,
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        params = {
            'grant_type': 'refresh_token',
            'refresh_token': self._refresh_token,
        }

        now = datetime.utcnow()

        response = self._session.post(_token_url, headers=headers, params=params)
        if not response.ok:
            raise BadResponseException('Failed to get access token', response)

        data = response.json()
        self._access_token = data['access_token']
        self._expires_at = now + timedelta(seconds=data['expires_in'])

    @require_access_token
    def search(self, release: Release) -> t.List[str]:
        queries = [
            quote(f'artist:{release.artist} album:{release.title}'),
            quote(f'album:{release.title}'),
        ]
        for q in queries:
            logger.info(f'Searching spotify for {q}')
            url = f'{_search_url}?q={q}&type=album&market=US'
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {self._access_token}',
                'Content-Type': 'application/json',
            }

            response = self._session.get(url, headers=headers)
            if not response.ok:
                raise BadResponseException('Failed to search Spotify', response)

            albums = response.json()['albums']['items']
            if not albums:
                continue

            logger.info(f'Found release for {q}')

            album = albums[0]

            response = self._session.get(
                _album_tracks_url.format(album_id=album['id']),
                headers=headers
            )

            if not response.ok:
                raise BadResponseException('Failed to get album tracks', response)

            tracks = response.json()['items']

            return [track['id'] for track in tracks]
        else:
            logger.warning(f'Couldn\'t find album {release.artist} - {release.title}')

        return []

    @require_access_token
    def add_tracks(self, track_ids: t.List[str]) -> None:
        logger.info('Adding tracks to playlist')
        url = _playlist_add_url.format(playlist_id=self._config.playlist_id)
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self._access_token}',
            'Content-Type': 'application/json',
        }
        body = {
            'uris': [f'spotify:track:{track_id}' for track_id in track_ids],
            'position': 0,
        }

        response = self._session.post(url, headers=headers, json=body)
        if not response.ok:
            raise BadResponseException('Failed to add tracks to playlist', response)
