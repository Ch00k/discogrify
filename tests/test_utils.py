import base64
import socket
from pathlib import Path
from unittest import mock

import pytest

from discogrify.spotify_client import Track
from discogrify.utils import (
    AuthConfig,
    capitalize_genres,
    deduplicate_tracks,
    extract_artist_id_from_url,
    is_port_in_use,
)


def test_capitalize_genres() -> None:
    genres = ["alternative rock", "art rock", "melancholia", "oxford indie", "permanent wave", "rock"]
    assert capitalize_genres(genres) == [
        "Alternative Rock",
        "Art Rock",
        "Melancholia",
        "Oxford Indie",
        "Permanent Wave",
        "Rock",
    ]


def test_is_port_in_use() -> None:
    assert is_port_in_use(65532) is False

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 65533))
    s.listen()

    assert is_port_in_use(65533) is True
    s.close()


def test_extract_artist_id_from_url() -> None:
    assert extract_artist_id_from_url("https://open.spotify.com/artist/foobar") == "foobar"
    assert extract_artist_id_from_url("https://open.spotify.com/artist/foobar/") == "foobar"

    with pytest.raises(RuntimeError):
        extract_artist_id_from_url("https://foo.bar/baz")

    with pytest.raises(RuntimeError):
        extract_artist_id_from_url("https://open.spotify.com/album/foobar")

    with pytest.raises(RuntimeError):
        extract_artist_id_from_url("https://open.spotify.com/artist/")


@mock.patch("discogrify.utils.is_port_in_use")
def test_auth_config(m_is_port_in_use: mock.Mock, tmp_path: Path) -> None:
    auth_config_file = tmp_path / "auth_config"
    auth_config_file.write_bytes(
        base64.b85encode("foobar\nhttp://127.0.0.1:2000\nhttp://127.0.0.1:3000\nhttp://127.0.0.1:4000".encode())
    )
    auth_config = AuthConfig.from_file(auth_config_file)

    assert auth_config.client_id == "foobar"
    assert auth_config.redirect_urls == ["http://127.0.0.1:2000", "http://127.0.0.1:3000", "http://127.0.0.1:4000"]

    m_is_port_in_use.side_effect = [True, True, False]

    assert auth_config.pick_redirect_url() == "http://127.0.0.1:4000"

    m_is_port_in_use.reset_mock()
    m_is_port_in_use.side_effect = [True, True, True]

    with pytest.raises(RuntimeError, match=r"All ports are in use"):
        auth_config.pick_redirect_url()


def test_dedupicate_tracks() -> None:
    track_1 = Track(id="foo", url="foo", name="foo")
    track_2 = Track(id="bar", url="bar", name="bar")
    track_3 = Track(id="baz", url="baz", name="baz")
    track_4 = Track(id="qux", url="qux", name="qux")

    assert deduplicate_tracks([], []) == []
    assert deduplicate_tracks([track_1, track_2, track_3, track_4], []) == []
    assert set(deduplicate_tracks([], [track_1, track_2, track_3, track_4])) == set(
        [track_1, track_2, track_3, track_4]
    )
    assert set(deduplicate_tracks([track_1, track_2], [track_1, track_2, track_3, track_4])) == set([track_3, track_4])
    assert set(deduplicate_tracks([track_1, track_2], [track_3, track_4])) == set([track_3, track_4])
