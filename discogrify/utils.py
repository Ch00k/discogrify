import re
from typing import TYPE_CHECKING
from urllib.parse import urlparse

if TYPE_CHECKING:
    from discogrify.spotify_client import Track


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
