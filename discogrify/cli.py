import itertools
import logging
from pathlib import Path

import click
from spotipy.cache_handler import CacheFileHandler

from . import config, spotify_client, utils
from .spotify_client import ClientError

logging.disable()

ALBUM_SORT_ORDER = {"album": 0, "single": 1, "compilation": 2}


class InvalidArtistURL(Exception):
    pass


def create_client() -> spotify_client.Client:
    return spotify_client.Client(
        scope=config.SPOTIFY_AUTH_SCOPE,
        redirect_uri=config.SPOTIFY_AUTH_REDIRECT_URL,
        open_browser=True,
        cache_handler=CacheFileHandler(cache_path=config.D8Y_AUTH_CACHE_FILE),
    )


def extract_artist_id_from_url(_: click.Context, __: click.Parameter, value: str) -> str:
    try:
        return utils.extract_artist_id_from_url(value)
    except RuntimeError:
        raise click.BadParameter("Invalid Spotify artist URL")


@click.group()
def cli() -> None:
    Path.mkdir(config.D8Y_AUTH_CACHE_DIR, parents=True, exist_ok=True)


@cli.command()
def authenticate() -> None:
    create_client()
    click.echo("Authentication successful")


@cli.command()
@click.argument("artist_url", callback=extract_artist_id_from_url)
@click.option("-t", "--playlist-title", help="Playlist title. Default: '<artist_name> discography'")
@click.option("-d", "--playlist-description", help="Playlist description. Default: 'Created with discogrify'")
@click.option("-p", "--public", default=True, help="Make playlist public. Default: true")
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
def create(
    artist_url: str,
    playlist_title: str,
    playlist_description: str,
    public: bool,
    with_singles: bool,
    with_compilations: bool,
) -> None:
    """Create a discography playlist of an artist defined by the ARTIST_URL.

    The ARTIST_URL must be a https://open.spotify.com/artist/<ID> URL, where <ID> is the Spotify artist ID.
    Example: https://open.spotify.com/artist/6uothxMWeLWIhsGeF7cyo4

    The ARTIST_URL can be found in browser URL bar while on the artist's page on Spotify.
    """
    client = create_client()

    try:
        artist = client.get_artist(artist_url)
    except ClientError as e:
        click.echo(e, err=True)
        raise click.exceptions.Exit(1)

    click.echo(f"Artist: {artist.name} ({', '.join(artist.genres)})")
    click.echo()

    if not playlist_title:
        playlist_title = f"{artist.name} discography"

    if not playlist_description:
        playlist_description = "Created with discogrify"

    albums = list(
        itertools.chain.from_iterable(
            client.get_artist_albums(artist=artist, singles=with_singles, compilations=with_compilations)
        )
    )
    albums.sort(key=lambda x: (ALBUM_SORT_ORDER[x.type], x.release_year))

    tracks = []

    legend = "(A - Album"
    if with_singles:
        legend += ", S - Single"
    if with_compilations:
        legend += ", C - Compilation"
    legend += ")"

    click.echo("Albums:")
    click.echo(legend)
    for album in albums:
        click.echo(f"{album.type[0].upper()} {album.release_year} {album.name}")
        tracks.extend(list(itertools.chain.from_iterable(client.get_album_tracks(album))))

    click.echo(f"Total albums: {len(albums)}")
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
            if my_playlist.name == playlist_title and my_playlist.description == playlist_description:
                playlist = my_playlist

                playlist_tracks = list(itertools.chain.from_iterable(client.get_playlist_tracks(playlist)))

                click.echo(f"Playlist '{playlist_title}' already exists and contains {len(playlist_tracks)} tracks")

                tracks = utils.deduplicate_tracks(playlist_tracks, tracks)
                if tracks:
                    click.echo(f"Updating playlist with {len(tracks)} new tracks")
                else:
                    click.echo("No new tracks to be added")
                    raise click.exceptions.Exit(0)

    if playlist is None:
        click.echo(f"Creating playlist '{playlist_title}'")
        playlist = client.create_my_playlist(name=playlist_title, description=playlist_description, public=public)

    click.echo()

    click.echo(f"Adding {len(tracks)} tracks to playlist")
    client.add_tracks_to_playlist(playlist=playlist, tracks=tracks)

    click.echo()
    click.echo(f"Done. Playlist URL: {playlist.url}")
