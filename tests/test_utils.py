from discogrify.utils import capitalize_genres


def test_capitalize_genres():
    genres = ["alternative rock", "art rock", "melancholia", "oxford indie", "permanent wave", "rock"]
    assert capitalize_genres(genres) == [
        "Alternative Rock",
        "Art Rock",
        "Melancholia",
        "Oxford Indie",
        "Permanent Wave",
        "Rock",
    ]
