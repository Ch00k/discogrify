from typing import Generator, Optional

import pytest

from discogrify import cli

playlist_id: Optional[str] = None


@pytest.fixture()
def delete_playlist() -> Generator:
    yield

    client = cli.create_client()

    if playlist_id is not None:
        client.delete_my_playlist(playlist_id)
