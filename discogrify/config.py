from pathlib import Path

D8Y_AUTH_CACHE_DIR = Path.home() / ".cache/discogrify"
D8Y_AUTH_CACHE_FILE = D8Y_AUTH_CACHE_DIR / "auth"
SPOTIFY_AUTH_SCOPE = "playlist-modify-private playlist-modify-public"
SPOTIFY_AUTH_REDIRECT_URL = "http://localhost:7891"
