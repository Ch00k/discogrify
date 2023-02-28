from typing import Generator, Optional

import pytest

from discogrify import cli, config

from . import config as test_config

playlist_id: Optional[str] = None


@pytest.fixture()
def setup_auth() -> None:
    if config.D8Y_AUTH_CACHE_FILE.exists() and config.D8Y_AUTH_CACHE_FILE.stat().st_size > 0:
        return

    config.D8Y_AUTH_CACHE_FILE.write_text(test_config.D8Y_AUTH_CACHE_DATA)


@pytest.fixture()
def delete_playlist() -> Generator:
    yield

    client = cli.create_client()

    if playlist_id is not None:
        client.delete_my_playlist(playlist_id)
