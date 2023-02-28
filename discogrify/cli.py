import itertools
import logging
from pathlib import Path

import click
from spotipy.cache_handler import CacheFileHandler
from tabulate import tabulate

from . import config, spotify_client, utils
from .spotify_client import ClientError

logging.disable()

ALBUM_SORT_ORDER = {"album": 0, "single": 1, "compilation": 2}
CONTEXT_SETTINGS = {"max_content_width": 120}


def create_client(open_browser: bool = True) -> spotify_client.Client:
    auth_config = utils.AuthConfig.from_file(config.D8Y_AUTH_CONFIG_FILE)

    return spotify_client.Client(
        client_id=auth_config.client_id,
        scope=" ".join(config.D8Y_AUTH_SCOPE),
        redirect_uri=auth_config.pick_redirect_url(),
        open_browser=open_browser,
        cache_handler=CacheFileHandler(cache_path=config.D8Y_AUTH_CACHE_FILE),
    )


def extract_artist_id_from_url(_: click.Context, __: click.Parameter, value: str) -> str:
    try:
        return utils.extract_artist_id_from_url(value)
    except RuntimeError:
        raise click.BadParameter("Must be a https://open.spotify.com/artist/<ID> URL")


@click.group(context_settings=CONTEXT_SETTINGS)
def cli() -> None:
    Path.mkdir(config.D8Y_AUTH_CACHE_FILE.parent, parents=True, exist_ok=True)


@cli.command()
@click.option("-l", "--headless", is_flag=True, help="Run in headless mode (don't attempt to open a browser)")
def login(headless: bool) -> None:
    """Authenticate the app with Spotify"""
    try:
        create_client(open_browser=not headless)
    except ClientError as e:
        click.echo("Login failed")
        click.echo(e, err=True)
        raise click.exceptions.Exit(1)
    else:
        click.echo("Login successful")


@cli.command()
def logout() -> None:
    """Remove app's authentication credentials"""
    try:
        config.D8Y_AUTH_CACHE_FILE.unlink()
    except FileNotFoundError:
        click.echo("Not logged in")
        raise click.exceptions.Exit(1)
    else:
        click.echo("Logout successful")


@cli.command()
@click.argument("artist_url", callback=extract_artist_id_from_url)
@click.option(
    "-t",
    "--playlist-title",
    help="Default playlist title is 'ARTIST_NAME (by d8y)'. Use this option to provide a different title",
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
    help="Playlist is created private by default. Provide this flag if you prefer it to be public",
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
    public: bool,
    with_singles: bool,
    with_compilations: bool,
    yes: bool,
) -> None:
    """Create a discography playlist of an artist defined by the ARTIST_URL

    The ARTIST_URL must be a https://open.spotify.com/artist/<ID> URL, where <ID> is the Spotify artist ID.
    Example: https://open.spotify.com/artist/6uothxMWeLWIhsGeF7cyo4

    The ARTIST_URL can be found in browser URL bar while on the artist's page on Spotify.

    By default the discography playslist includes all albums and singles, but no compilations. This behaviour can be
    altered by --with-singles/--without-singles and --with-compilations/--without-compilations options.
    """
    try:
        client = create_client()
    except ClientError as e:
        click.echo(e, err=True)
        raise click.exceptions.Exit(1)

    try:
        artist = client.get_artist(artist_url)
    except ClientError as e:
        click.echo(e, err=True)
        raise click.exceptions.Exit(1)

    click.echo(f"{artist.name}: {', '.join(artist.genres)}")

    if not playlist_title:
        playlist_title = f"{artist.name} (by d8y)"

    try:
        albums = list(
            itertools.chain.from_iterable(
                client.get_artist_albums(artist=artist, singles=with_singles, compilations=with_compilations)
            )
        )
    except ClientError as e:
        click.echo(e, err=True)
        raise click.exceptions.Exit(1)

    if not albums:
        click.echo("No albums found")
        raise click.exceptions.Exit(0)

    click.echo()

    albums.sort(key=lambda x: (ALBUM_SORT_ORDER[x.type], x.release_year))
    albums_table = [[a.type.capitalize(), a.release_year, a.num_tracks, a.name] for a in albums]

    tracks = []
    for album in albums:
        try:
            tracks.extend(list(itertools.chain.from_iterable(client.get_album_tracks(album))))
        except ClientError as e:
            click.echo(e, err=True)
            raise click.exceptions.Exit(1)

    if not tracks:
        click.echo("No tracks found")
        raise click.exceptions.Exit(0)

    albums_table += [["", "", len(tracks), ""]]
    click.echo(tabulate(albums_table, headers=["Type", "Year", "Tracks", "Title"]))
    click.echo()

    playlist = None

    try:
        my_playlists = list(itertools.chain.from_iterable(client.get_my_playlists()))
    except ClientError as e:
        click.echo(e, err=True)
        raise click.exceptions.Exit(1)

    for my_playlist in my_playlists:
        if my_playlist.name != playlist_title:
            continue

        playlist = my_playlist

        try:
            playlist_tracks = list(itertools.chain.from_iterable(client.get_playlist_tracks(playlist)))
        except ClientError as e:
            click.echo(e, err=True)
            raise click.exceptions.Exit(1)

        click.echo(
            f"Playlist '{playlist_title}' already exists and contains "
            f"{len(playlist_tracks)} track{'' if len(tracks) == 1 else 's'}"
        )

        tracks = utils.deduplicate_tracks(playlist_tracks, tracks)
        if tracks:
            if not yes:
                click.confirm(
                    f"Update playlist with {len(tracks)} new track{'' if len(tracks) == 1 else 's'}?",
                    default=True,
                    abort=True,
                )
        else:
            click.echo("No new tracks to be added")
            raise click.exceptions.Exit(0)

    if playlist is None:
        click.echo(f"Creating playlist '{playlist_title}'")
        if not yes:
            click.confirm("Continue?", default=True, abort=True)
        try:
            playlist = client.create_my_playlist(name=playlist_title, description=playlist_description, public=public)
        except ClientError as e:
            click.echo(e, err=True)
            raise click.exceptions.Exit(1)

    click.echo()

    click.echo(f"Adding {len(tracks)} track{'' if len(tracks) == 1 else 's'} to playlist")
    try:
        client.add_tracks_to_playlist(playlist=playlist, tracks=tracks)
    except ClientError as e:
        click.echo(e, err=True)
        raise click.exceptions.Exit(1)

    click.echo(f"Playlist ready: {playlist.url}")
