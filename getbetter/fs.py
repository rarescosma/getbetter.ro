import os
from pathlib import Path
from typing import Iterable, List

from .fun import flatmap


def all_subdirs(p: Path) -> List[Path]:
    """ Return all subdirs of the given path (following symlinks).
    """
    return list(
        map(
            lambda _: p / _,
            flatmap(lambda _: _[1], os.walk(p.as_posix(), followlinks=True)),
        )
    )


def is_link_to_dir(p: Path) -> bool:
    return p.is_symlink() and p.resolve().is_dir()


def multiglob(start_dir: Path, extensions: Iterable[str]) -> Iterable[Path]:
    """ Recursively glob multiple file extensions starting at start_dir.
    """
    for ext in extensions:
        yield from start_dir.rglob(f"*.{ext}")
    for subdir in all_subdirs(start_dir):
        yield from multiglob(subdir, extensions)
