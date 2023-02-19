from pathlib import Path

D8Y_AUTH_CACHE_DIR = Path.home() / ".cache/discogrify"
D8Y_AUTH_CACHE_FILE = D8Y_AUTH_CACHE_DIR / "auth"
SPOTIFY_AUTH_SCOPE = [
    "playlist-read-private",
    "playlist-modify-private",
    "playlist-modify-public",
]
