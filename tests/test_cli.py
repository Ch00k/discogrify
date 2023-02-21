from pathlib import Path
from typing import Callable

import pytest
from click.testing import CliRunner

from discogrify.cli import CONTEXT_SETTINGS, cli

OUTPUT_PATH = Path(__file__).parent / "output"


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
