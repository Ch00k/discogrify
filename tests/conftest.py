import os
from pathlib import Path
from typing import Generator

import pytest

from discogrify import config


@pytest.fixture()
def setup_auth(tmp_path: Path) -> Generator:
    orig_path = config.D8Y_AUTH_CACHE_FILE
    temp_auth_cache_file = tmp_path / "auth"
    temp_auth_cache_file.write_text(os.environ["D8Y_TEST_AUTH"])
    config.D8Y_AUTH_CACHE_FILE = temp_auth_cache_file
    yield
    config.D8Y_AUTH_CACHE_FILE = orig_path
