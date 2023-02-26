from pathlib import Path
from typing import Callable

import pytest
from click.testing import CliRunner

from discogrify.cli import CONTEXT_SETTINGS, cli

from . import conftest

OUTPUT_PATH = Path(__file__).parent / "data/output"
ARTIST_URL = "https://open.spotify.com/artist/432R46LaYsJZV2Gmc4jUV5"


def get_playlist_id(output: str) -> str:
    return output.strip().split()[-1].split("/")[-1]


@pytest.mark.parametrize("subcommand", ["", "login", "logout", "create"])
def test_help(subcommand: str) -> None:
    cmd = [subcommand, "--help"] if subcommand else ["--help"]
    output_file = f"help_{subcommand}.txt" if subcommand else "help.txt"

    runner = CliRunner()
    result = runner.invoke(cli, cmd, terminal_width=CONTEXT_SETTINGS["max_content_width"])

    assert result.exit_code == 0
    assert result.output == open(OUTPUT_PATH / output_file).read()


def test_login(setup_auth: Callable) -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["login"], terminal_width=CONTEXT_SETTINGS["max_content_width"])

    assert result.exit_code == 0
    assert result.output == "Login successful\n"


def test_logout(setup_auth: Callable) -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["logout"], terminal_width=CONTEXT_SETTINGS["max_content_width"])

    assert result.exit_code == 0
    assert result.output == "Logout successful\n"

    runner = CliRunner()
    result = runner.invoke(cli, ["logout"], terminal_width=CONTEXT_SETTINGS["max_content_width"])

    assert result.exit_code == 1
    assert result.output == "Not logged in\n"


def test_create(setup_auth: Callable, delete_playlist: Callable) -> None:
    runner = CliRunner()

    # Create with albums only
    result = runner.invoke(
        cli, ["create", ARTIST_URL, "--without-singles", "--yes"], terminal_width=CONTEXT_SETTINGS["max_content_width"]
    )
    assert result.exit_code == 0
    created_playlist_id = get_playlist_id(result.output)
    assert result.output == open(OUTPUT_PATH / "create_albums_only.txt").read().format(playlist_id=created_playlist_id)

    # Add singles
    result = runner.invoke(
        cli, ["create", ARTIST_URL, "--with-singles", "--yes"], terminal_width=CONTEXT_SETTINGS["max_content_width"]
    )
    assert result.exit_code == 0
    assert result.output == open(OUTPUT_PATH / "create_add_singles.txt").read().format(playlist_id=created_playlist_id)

    # Add compilations
    result = runner.invoke(
        cli,
        ["create", ARTIST_URL, "--with-singles", "--with-compilations", "--yes"],
        terminal_width=CONTEXT_SETTINGS["max_content_width"],
    )
    assert result.exit_code == 0
    assert result.output == open(OUTPUT_PATH / "create_add_compilations.txt").read().format(
        playlist_id=created_playlist_id
    )

    # Pass playlist ID to delete_playlist fixture
    conftest.playlist_id = created_playlist_id
