import json
from typing import Callable, Generator, Optional

import pytest
from environs import Env

from discogrify import cli, config

playlist_id: Optional[str] = None


@pytest.fixture(scope="session")
def auth() -> None:
    env = Env()

    if auth_cache_data := env.str("D8Y_AUTH_CACHE_DATA", None):
        print(f"Writing D8Y_AUTH_CACHE_DATA to {config.D8Y_AUTH_CACHE_FILE}")
        config.D8Y_AUTH_CACHE_FILE.write_text(auth_cache_data)


@pytest.fixture(autouse=True, scope="session")
def env(auth: Callable) -> None:
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
