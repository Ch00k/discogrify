from pathlib import Path
from typing import List

from setuptools import find_packages, setup

from discogrify import __version__


def read_lines(file_path: Path) -> List[str]:
    with file_path.open("r") as f:
        return f.readlines()


setup(
    name="discogrify",
    version=__version__,
    description="Create discographies on Spotify",
    long_description=open("README.md").read(),
    author="Andrii Yurchuk",
    author_email="ay@mntw.re",
    license="Unlicense",
    url="https://github.com/Ch00k/discogrify",
    packages=find_packages(),
    include_package_data=True,
    install_requires=read_lines(Path(__file__).parent / "requirements.txt"),
    entry_points={
        "console_scripts": [
            "d8y = discogrify.cli:cli",
            "discogrify = discogrify.cli:cli",
        ],
    },
    classifiers=[
        "Topic :: Multimedia :: Sound/Audio",
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: The Unlicense (Unlicense)",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Operating System :: POSIX :: BSD",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
    ],
    keywords="spotify discography playlist",
)
