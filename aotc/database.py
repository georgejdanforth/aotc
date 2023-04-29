import psycopg


class DatabaseError(Exception):
    pass


_get_auth_code_query = 'SELECT code FROM authorization_code ORDERY BY created DESC LIMIT 1'

_set_auth_code_query = 'INSERT INTO authorization_code (code) VALUES (%s)'


class Database:
    def __init__(self, connection: psycopg.Connection) -> None:
        self._connection = connection

    def get_auth_code(self) -> str:
        with self._connection.cursor() as cursor:
            cursor.execute(_get_auth_code_query)
            result = cursor.fetchone()
            if result is None or len(result) == 0:
                raise DatabaseError('No authorization code found')
            return result[0]

    def set_auth_code(self, code: str) -> None:
        with self._connection.cursor() as cursor:
            cursor.execute(_set_auth_code_query, (code,))
            self._connection.commit()
