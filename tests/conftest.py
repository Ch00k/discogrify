import os
from pathlib import Path
from typing import Generator, Optional

import pytest

from discogrify import cli, config, spotify_client

playlist_id: Optional[str] = None


@pytest.fixture()
def setup_auth(tmp_path: Path) -> Generator:
    orig_path = config.D8Y_AUTH_CACHE_FILE
    temp_auth_cache_file = tmp_path / "auth"
    temp_auth_cache_file.write_text(os.environ["D8Y_TEST_AUTH"])
    config.D8Y_AUTH_CACHE_FILE = temp_auth_cache_file
    yield
    config.D8Y_AUTH_CACHE_FILE = orig_path


@pytest.fixture()
def delete_playlist() -> Generator:
    yield
    client = cli.create_client()

    if playlist_id is not None:
        client.delete_my_playlist(
            spotify_client.Playlist(id=playlist_id, url="dummy", name="dummy", description="dummy")
        )
