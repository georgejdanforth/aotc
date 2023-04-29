from dataclasses import dataclass


@dataclass
class SpotifyConfig:
    client_id: str
    client_secret: str
    playlist_id: str


@dataclass
class Config:
    title: str
    spotify: SpotifyConfig

    def __post_init__(self) -> None:
        self.spotify = SpotifyConfig(**self.spotify)  # type: ignore
