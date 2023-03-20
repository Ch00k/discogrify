from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Generator, Optional

from spotipy import Spotify, SpotifyException, SpotifyOauthError
from spotipy.cache_handler import CacheHandler
from spotipy.oauth2 import SpotifyPKCE

from .utils import capitalize_genres, deduplicate_tracks

logging.basicConfig(level=logging.INFO)

PAGE_SIZE = 50
PAGE_SIZE_PLAYLIST_TRACKS = 100


@dataclass
class SpotifyEntity:
    id: str
    url: str


@dataclass
class User(SpotifyEntity):
    name: str


@dataclass
class Artist(SpotifyEntity):
    name: str
    genres: list[str]
    followers: int


@dataclass
class Album(SpotifyEntity):
    name: str
    type: str
    release_year: str
    num_tracks: int


@dataclass
class Track(SpotifyEntity):
    name: str

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass
class Playlist(SpotifyEntity):
    name: str
    description: str


class ClientError(Exception):
    pass


class Client:
    def __init__(
        self,
        client_id: str,
        scope: str,
        redirect_uri: Optional[str] = None,
        open_browser: bool = True,
        cache_handler: Optional[CacheHandler] = None,
    ) -> None:
        self.auth_manager = SpotifyPKCE(
            client_id=client_id,
            scope=scope,
            redirect_uri=redirect_uri,
            open_browser=open_browser,
            cache_handler=cache_handler,
        )
        self.client = Spotify(auth_manager=self.auth_manager)

        try:
            res = self.client.me()
        except (SpotifyException, SpotifyOauthError) as e:
            raise ClientError(e)

        if res is None:
            raise ClientError("Internal client error")

        self.me = User(name=res["display_name"], id=res["id"], url=res["external_urls"]["spotify"])

    def search_artists(self, term: str) -> Generator[list[Artist], None, None]:  # pragma: no cover
        try:
            res = self.client.search(q="artist:" + term, type="artist", limit=PAGE_SIZE)
        except (SpotifyException, SpotifyOauthError) as e:
            raise ClientError(e)

        if res is None:
            raise ClientError("Internal client error")

        for page in self._paginate_search_result(res):
            yield [
                Artist(
                    id=a["id"],
                    url=a["external_urls"]["spotify"],
                    name=a["name"],
                    genres=capitalize_genres(a["genres"]),
                    followers=a["followers"]["total"],
                )
                for a in page
            ]

    def get_artist(self, artist_id: str) -> Artist:
        try:
            res = self.client.artist(artist_id)
        except (SpotifyException, SpotifyOauthError) as e:
            raise ClientError(e)

        if res is None:
            raise ClientError("Internal client error")

        return Artist(
            id=res["id"],
            url=res["external_urls"]["spotify"],
            name=res["name"],
            genres=capitalize_genres(res["genres"]),
            followers=res["followers"]["total"],
        )

    def get_artist_albums(
        self,
        artist: Artist,
        albums: bool = True,
        singles: bool = True,
        compilations: bool = False,
        appears_on: bool = False,
    ) -> Generator[list[Album], None, None]:
        album_types = []

        if albums:
            album_types.append("album")
        if singles:
            album_types.append("single")
        if compilations:
            album_types.append("compilation")
        if appears_on:
            album_types.append("appears_on")

        try:
            res = self.client.artist_albums(artist.id, album_type=",".join(album_types), limit=PAGE_SIZE)
        except (SpotifyException, SpotifyOauthError) as e:
            raise ClientError(e)

        if res is None:
            raise ClientError("Internal client error")

        for page in self._paginate_list_result(res):
            yield [
                Album(
                    id=a["id"],
                    url=a["external_urls"]["spotify"],
                    name=a["name"],
                    type=a["album_type"],
                    release_year=a["release_date"].split("-")[0],
                    num_tracks=a["total_tracks"],
                )
                for a in page
            ]

    def get_album_tracks(self, album: Album) -> Generator[list[Track], None, None]:
        try:
            res = self.client.album_tracks(album.id, limit=PAGE_SIZE)
        except (SpotifyException, SpotifyOauthError) as e:
            raise ClientError(e)

        if res is None:
            raise ClientError("Internal client error")

        for page in self._paginate_list_result(res):
            yield [
                Track(
                    name=t["name"],
                    id=t["id"],
                    url=t["external_urls"]["spotify"],
                )
                for t in page
            ]

    def get_my_playlists(self) -> Generator[list[Playlist], None, None]:
        try:
            res = self.client.current_user_playlists(limit=PAGE_SIZE)
        except (SpotifyException, SpotifyOauthError) as e:
            raise ClientError(e)

        if res is None:
            raise ClientError("Internal client error")

        for page in self._paginate_list_result(res):
            yield [
                Playlist(
                    name=p["name"],
                    description=p["description"],
                    id=p["id"],
                    url=p["external_urls"]["spotify"],
                )
                for p in page
            ]

    def get_user_playlists(self, user: User) -> Generator[list[Playlist], None, None]:  # pragma: no cover
        try:
            res = self.client.user_playlists(user=user.id, limit=PAGE_SIZE)
        except (SpotifyException, SpotifyOauthError) as e:
            raise ClientError(e)

        if res is None:
            raise ClientError("Internal client error")

        for page in self._paginate_list_result(res):
            yield [
                Playlist(
                    name=p["name"],
                    description=p["description"],
                    id=p["id"],
                    url=p["external_urls"]["spotify"],
                )
                for p in page
            ]

    def get_playlist(self, playlist_id: str) -> Playlist:
        try:
            res = self.client.playlist(playlist_id)
        except (SpotifyException, SpotifyOauthError) as e:
            raise ClientError(e)

        if res is None:
            raise ClientError("Internal client error")

        return Playlist(
            name=res["name"], description=res["description"], id=res["id"], url=res["external_urls"]["spotify"]
        )

    def create_my_playlist(self, name: str, description: Optional[str] = None, public: bool = True) -> Playlist:
        if description is None:
            description = ""

        try:
            res = self.client.user_playlist_create(self.me.id, name=name, public=public, description=description)
        except (SpotifyException, SpotifyOauthError) as e:
            raise ClientError(e)

        if res is None:
            raise ClientError("Internal client error")

        return Playlist(name=name, description=description, id=res["id"], url=res["external_urls"]["spotify"])

    def delete_my_playlist(self, playlist_id: str) -> None:
        try:
            self.client.current_user_unfollow_playlist(playlist_id)
        except (SpotifyException, SpotifyOauthError) as e:
            raise ClientError(e)

    def add_tracks_to_playlist(self, playlist: Playlist, tracks: list[Track]) -> None:
        for i in range(0, len(tracks), PAGE_SIZE_PLAYLIST_TRACKS):
            try:
                self.client.playlist_add_items(playlist.id, [t.id for t in tracks[i : i + PAGE_SIZE_PLAYLIST_TRACKS]])
            except (SpotifyException, SpotifyOauthError) as e:
                # TODO: rollback?
                raise ClientError(e)

    def get_playlist_tracks(self, playlist: Playlist) -> Generator[list[Track], None, None]:
        try:
            res = self.client.playlist_items(playlist.id, limit=PAGE_SIZE_PLAYLIST_TRACKS)
        except (SpotifyException, SpotifyOauthError) as e:
            raise ClientError(e)

        if res is None:
            raise ClientError("Internal client error")

        for page in self._paginate_list_result(res):
            yield [
                Track(
                    name=t["track"]["name"],
                    id=t["track"]["id"],
                    url=t["track"]["external_urls"]["spotify"],
                )
                for t in page
            ]

    def _paginate_search_result(
        self, result: dict[str, Any]
    ) -> Generator[list[dict[str, Any]], None, None]:  # pragma: no cover
        if len(result) > 1:
            raise ClientError("Only one term at a time!")

        key = list(result)[0]
        yield result[key]["items"]

        while result[key]["next"]:
            try:
                next_page = self.client.next(result[key])
            except (SpotifyException, SpotifyOauthError) as e:
                raise ClientError(e)

            if next_page is None:
                raise ClientError("Internal client error")

            yield next_page[key]["items"]

            result = next_page

    def _paginate_list_result(self, result: dict[str, Any]) -> Generator[list[dict[str, Any]], None, None]:
        yield result["items"]

        while result["next"]:
            try:
                next_page = self.client.next(result)
            except (SpotifyException, SpotifyOauthError) as e:
                raise ClientError(e)

            if next_page is None:
                raise ClientError("Internal client error")

            yield next_page["items"]

            result = next_page


def main() -> None:  # pragma: no cover
    artist_search_term = input("Input artist search term: ")

    client = Client(client_id="foobar", scope="playlist-modify-private playlist-modify-public")

    artist = None
    artist_tracks = []
    playlist = None

    search_results_generator = client.search_artists(term=artist_search_term)
    page_num = 1

    while True:
        try:
            results = next(search_results_generator)
        except StopIteration:
            print("No more results")
            break

        print(f"Page {page_num}")

        for i, a in enumerate(results, start=1):
            print(i, a)

        print()
        page_num += 1

        artist_num_imput = input("Please pick an artist and input its number, or Enter to show next page: ")
        if artist_num_imput:
            artist_num = int(artist_num_imput)
            artist = results[artist_num - 1]
            break

    if artist is None:
        print("No artist selected. Exiting")
        return

    playlist_name = artist.name
    playlist_description = f"{playlist_name} discography by d8y"

    for album_page in client.get_artist_albums(artist=artist):
        for album in album_page:
            for track_page in client.get_album_tracks(album):
                for track in track_page:
                    artist_tracks.append(track)

    for my_playlist_page in client.get_my_playlists():
        for my_playlist in my_playlist_page:
            if my_playlist.name == playlist_name and my_playlist.description == playlist_description:
                print(f"Playlist {playlist_name} already exists: {my_playlist}")
                playlist = my_playlist

                # TODO: Getting the entire result in a single list should be easier
                playlist_tracks = []
                for playlist_tracks_page in client.get_playlist_tracks(playlist=playlist):
                    playlist_tracks.extend(playlist_tracks_page)

                print(f"Initial number of tracks: {len(artist_tracks)}")
                artist_tracks = deduplicate_tracks(playlist_tracks, artist_tracks)
                print(f"Number of tracks after deduplication: {len(artist_tracks)}")

    if playlist is None:
        playlist = client.create_my_playlist(name=playlist_name, description=playlist_description)
        print(f"Created playlist {playlist}")

    if artist_tracks:
        print(f"Adding {len(artist_tracks)} tracks to playlist")
        client.add_tracks_to_playlist(playlist=playlist, tracks=artist_tracks)
    else:
        print("No tracks to be added")


if __name__ == "__main__":  # pragma: no cover
    main()
