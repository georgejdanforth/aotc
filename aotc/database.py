import typing as t

import psycopg


class DatabaseError(Exception):
    pass


_get_refresh_token_query: t.LiteralString = 'SELECT token FROM refresh_token ORDER BY created DESC LIMIT 1'

_set_refresh_token_query: t.LiteralString = 'INSERT INTO refresh_token (token) VALUES (%s)'


class Database:
    def __init__(self, connection: psycopg.Connection) -> None:
        self._connection = connection

    def get_refresh_token(self) -> str:
        with self._connection.cursor() as cursor:
            cursor.execute(_get_refresh_token_query)
            result = cursor.fetchone()
            if result is None or len(result) == 0:
                raise DatabaseError('No authorization code found')
            return result[0]

    def set_refresh_token(self, code: str) -> None:
        with self._connection.cursor() as cursor:
            cursor.execute(_set_refresh_token_query, (code,))
            self._connection.commit()
