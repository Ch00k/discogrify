import json
from pathlib import Path

from environs import Env

from discogrify import cli, config

if __name__ == "__main__":
    print(f"D8Y_AUTH_CONFIG_FILE: {config.D8Y_AUTH_CONFIG_FILE}")
    print(f"D8Y_AUTH_CACHE_FILE: {config.D8Y_AUTH_CACHE_FILE}")

    env = Env()

    if auth_cache_data := env.str("D8Y_AUTH_CACHE_DATA", None):
        print(f"Writing D8Y_AUTH_CACHE_DATA to {config.D8Y_AUTH_CACHE_FILE}")
        print(f"Token expiration timestamp (before auth attempt): {json.loads(auth_cache_data).get('expires_at')}")
        Path.mkdir(config.D8Y_AUTH_CACHE_FILE.parent, parents=True, exist_ok=True)
        config.D8Y_AUTH_CACHE_FILE.touch()
        config.D8Y_AUTH_CACHE_FILE.write_text(auth_cache_data)

    cli.create_client()

    with open(config.D8Y_AUTH_CACHE_FILE) as f:
        auth_cache_data = f.read()
    print(f"Token expiration timestamp (after auth attempt): {json.loads(auth_cache_data).get('expires_at')}")
