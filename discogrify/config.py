from pathlib import Path

D8Y_AUTH_CACHE_FILE = Path.home() / ".config/d8y" / "auth"
D8Y_SPOTIFY_AUTH_SCOPE = [
    "playlist-read-private",
    "playlist-modify-private",
    "playlist-modify-public",
]
