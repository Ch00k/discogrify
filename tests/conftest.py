import json
from typing import Generator, Optional

import pytest

from discogrify import cli, config

playlist_id: Optional[str] = None


@pytest.fixture(autouse=True, scope="session")
def env() -> None:
    print()
    print(f"D8Y_AUTH_CONFIG_FILE: {config.D8Y_AUTH_CONFIG_FILE}")
    print(f"D8Y_AUTH_CACHE_FILE: {config.D8Y_AUTH_CACHE_FILE}")

    with open(config.D8Y_AUTH_CACHE_FILE) as f:
        auth_cache_data = f.read()
    print(f"Token expiration timestamp: {json.loads(auth_cache_data).get('expires_at')}")


@pytest.fixture()
def delete_playlist() -> Generator:
    yield

    client = cli.create_client()

    if playlist_id is not None:
        client.delete_my_playlist(playlist_id)
