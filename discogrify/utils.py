from __future__ import annotations

import base64
import re
import socket
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlparse

if TYPE_CHECKING:
    from discogrify.spotify_client import Track


@dataclass
class AuthConfig:
    client_id: str
    redirect_urls: list[str]

    @classmethod
    def from_file(cls, file_path: Path) -> "AuthConfig":
        with open(file_path, "rb") as f:
            data = f.read()

        lines = base64.b85decode(data).decode().split()
        return AuthConfig(client_id=lines[0], redirect_urls=lines[1:])

    def pick_redirect_url(self) -> str:
        for url in self.redirect_urls:
            port = url.split(":")[-1]
            if not is_port_in_use(int(port)):
                return url
        else:
            raise RuntimeError("All ports are in use")


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def capitalize_genres(genres: list[str]) -> list[str]:
    return [" ".join([c.capitalize() for c in g.split()]) for g in genres]


def deduplicate_tracks(tracks_in_playlist: list["Track"], new_tracks: list["Track"]) -> list["Track"]:
    return list(set(new_tracks) - set(tracks_in_playlist))


def extract_artist_id_from_url(url: str) -> str:
    res = urlparse(url)

    if res.netloc != "open.spotify.com":
        raise RuntimeError

    path_pattern = re.compile(r"/artist/(\w*).*")
    match = path_pattern.match(res.path)
    if match is None:
        raise RuntimeError

    artist_id = match.group(1)
    if not artist_id:
        raise RuntimeError

    return artist_id
