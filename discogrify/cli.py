import itertools
import logging
from pathlib import Path

import click
from spotipy.cache_handler import CacheFileHandler

from . import config, spotify_client, utils
from .spotify_client import ClientError

logging.disable()

ALBUM_SORT_ORDER = {"album": 0, "single": 1, "compilation": 2}
CONTEXT_SETTINGS = {"max_content_width": 120}


class InvalidArtistURL(Exception):
    pass


def create_client(open_browser: bool = True) -> spotify_client.Client:
    auth_config = utils.AuthConfig.from_file(Path(__file__).parent / "auth_config")
    return spotify_client.Client(
        client_id=auth_config.client_id,
        scope=" ".join(config.SPOTIFY_AUTH_SCOPE),
        redirect_uri=auth_config.pick_redirect_url(),
        open_browser=open_browser,
        cache_handler=CacheFileHandler(cache_path=config.D8Y_AUTH_CACHE_FILE),
    )


def extract_artist_id_from_url(_: click.Context, __: click.Parameter, value: str) -> str:
    try:
        return utils.extract_artist_id_from_url(value)
    except RuntimeError:
        raise click.BadParameter("Invalid Spotify artist URL")


@click.group(context_settings=CONTEXT_SETTINGS)
def cli() -> None:
    Path.mkdir(config.D8Y_AUTH_CACHE_DIR, parents=True, exist_ok=True)


@cli.command()
@click.option("-l", "--headless", is_flag=True, help="Run in headless mode (don't attempt to open a browser)")
def login(headless: bool) -> None:
    create_client(open_browser=not headless)
    click.echo("Login successful")


@cli.command()
def logout() -> None:
    try:
        config.D8Y_AUTH_CACHE_FILE.unlink()
    except FileNotFoundError:
        click.echo("Not logged in")
    else:
        click.echo("Logout successful")


@cli.command()
@click.argument("artist_url", callback=extract_artist_id_from_url)
@click.option(
    "-t",
    "--playlist-title",
    help="Default playlist title id 'ARTIST_NAME (by d8y)'. Use this option to provide a different title",
)
@click.option(
    "-d",
    "--playlist-description",
    default="",
    help="Playlist is created without a description by default. Use this option to specify a description",
)
@click.option(
    "-p",
    "--public",
    is_flag=True,
    default=False,
    help="Playlist is created private be default. Provide this flag if you prefer it to be public",
)
@click.option(
    "--with-singles/--without-singles",
    default=True,
    help="Include or exclude singles from the resulting discography. Default: include",
)
@click.option(
    "--with-compilations/--without-compilations",
    default=False,
    help="Include or exclude compilations from the resulting discography. Default: exclude",
)
@click.option(
    "-y",
    "--yes",
    is_flag=True,
    default=False,
    help="Answer 'yes' to all prompts (run non-interactively). Default: false",
)
def create(
    artist_url: str,
    playlist_title: str,
    playlist_description: str,
    playlist_is_public: bool,
    with_singles: bool,
    with_compilations: bool,
    yes: bool,
) -> None:
    """Create a discography playlist of an artist defined by the ARTIST_URL.

    The ARTIST_URL must be a https://open.spotify.com/artist/<ID> URL, where <ID> is the Spotify artist ID.
    Example: https://open.spotify.com/artist/6uothxMWeLWIhsGeF7cyo4

    The ARTIST_URL can be found in browser URL bar while on the artist's page on Spotify.

    By default the discography playslist includes all albums and singles, but no compilations. This behaviour can be
    altered by --with-singles/--without-singles and --with-compilations/--without-compilations options.
    """
    client = create_client()

    try:
        artist = client.get_artist(artist_url)
    except ClientError as e:
        click.echo(e, err=True)
        raise click.exceptions.Exit(1)

    click.echo(f"Artist: {artist.name} ({', '.join(artist.genres)})")

    if not playlist_title:
        playlist_title = f"{artist.name} (by d8y)"

    albums = list(
        itertools.chain.from_iterable(
            client.get_artist_albums(artist=artist, singles=with_singles, compilations=with_compilations)
        )
    )

    if not albums:
        click.echo("No albums found")
        raise click.exceptions.Exit(0)

    click.echo()

    albums.sort(key=lambda x: (ALBUM_SORT_ORDER[x.type], x.release_year))

    legend = "A - Album"
    if with_singles:
        legend += ", S - Single"
    if with_compilations:
        legend += ", C - Compilation"

    click.echo(f"Albums ({legend}, total: {len(albums)}):")
    click.echo(legend)

    tracks = []
    for album in albums:
        click.echo(f"{album.type[0].upper()} {album.release_year} {album.name}")
        tracks.extend(list(itertools.chain.from_iterable(client.get_album_tracks(album))))

    click.echo()

    if tracks:
        click.echo(f"Total tracks: {len(tracks)}")
    else:
        click.echo("No tracks found")
        raise click.exceptions.Exit(0)

    click.echo()

    playlist = None

    for my_playlist_page in client.get_my_playlists():
        for my_playlist in my_playlist_page:
            if my_playlist.name == playlist_title:
                playlist = my_playlist

                playlist_tracks = list(itertools.chain.from_iterable(client.get_playlist_tracks(playlist)))

                click.echo(f"Playlist '{playlist_title}' already exists and contains {len(playlist_tracks)} tracks")

                tracks = utils.deduplicate_tracks(playlist_tracks, tracks)
                if tracks:
                    click.echo(f"Updating playlist with {len(tracks)} new tracks")
                    if not yes:
                        click.confirm("Continue?", default=True, abort=True)
                else:
                    click.echo("No new tracks to be added")
                    raise click.exceptions.Exit(0)

    if playlist is None:
        click.echo(f"Creating playlist '{playlist_title}'")
        if not yes:
            click.confirm("Continue?", default=True, abort=True)
        playlist = client.create_my_playlist(
            name=playlist_title, description=playlist_description, public=playlist_is_public
        )

    click.echo()

    click.echo(f"Adding {len(tracks)} tracks to playlist")
    client.add_tracks_to_playlist(playlist=playlist, tracks=tracks)

    click.echo()
    click.echo(f"Playlist ready: {playlist.url}")
