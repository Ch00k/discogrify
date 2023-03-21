# discogrify

[![codecov](https://codecov.io/github/Ch00k/discogrify/branch/main/graph/badge.svg?token=VqiqnTAjJX)](https://codecov.io/github/Ch00k/discogrify)

_discogrify_ is a command line tool to create artist discographies as Spotify playlists.

## Installation

The easiest way to install _discogrify_ is with [pipx](https://pypa.github.io/pipx/) (see
[here](https://pypa.github.io/pipx/installation/) for installation of pipx itself):

```
pipx install discogrify
```

## Usage

First, authenticate with Spotify:

```
d8y authenticate
```

This will open a browser where you would be asked to login with your Spotify account and give _discogrify_ access to it.

When done, create your playlist by providing a Spotify artist URL to `d8y create`. For example the following command
will create a playlist with all albums and singles of Joy Division:

```
d8y create https://open.spotify.com/artist/432R46LaYsJZV2Gmc4jUV5
```

For more details on usage:

```
d8y create --help
```
