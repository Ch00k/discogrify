from pathlib import Path

from environs import Env

env = Env()

D8Y_AUTH_CONFIG_FILE = env.path("D8Y_AUTH_CONFIG_FILE", Path(__file__).parent / "auth_config")
D8Y_AUTH_CACHE_FILE = env.path("D8Y_AUTH_CACHE_FILE", Path.home() / ".config/d8y/auth")
D8Y_AUTH_SCOPE = env.list(
    "D8Y_SPOTIFY_AUTH_SCOPE", ["playlist-read-private", "playlist-modify-private", "playlist-modify-public"]
)
