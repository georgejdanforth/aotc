from dataclasses import dataclass


@dataclass
class SpotifyConfig:
    client_id: str
    client_secret: str
    playlist_id: str


@dataclass
class DatabaseConfig:
    host: str
    port: int
    user: str
    password: str
    database: str

    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}/{self.database}"


@dataclass
class Config:
    title: str
    spotify: SpotifyConfig
    database: DatabaseConfig

    def __post_init__(self) -> None:
        self.spotify = SpotifyConfig(**self.spotify)  # type: ignore
        self.database = DatabaseConfig(**self.database)  # type: ignore
