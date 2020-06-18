#!/usr/bin/env python3
"""
    Assumptions:
    * path names are unique => they can serve as keys in the hash cache
    * it would be nice to persist the hashes (but not necessary)
"""
import os
import time
from dataclasses import dataclass, replace
from multiprocessing import Pool
from pathlib import Path
from threading import Thread
from typing import List, Tuple

import sh
from devtools import debug
from pyinotify import Event

from .fs import multiglob
from .fun import flatmap
from .watch import start_notifier

RAW_GALLERIES: Path = Path(
    os.getenv("RAW_GALLERIES", "/pv/galleries/raw")
).resolve()
RESIZED_GALLERIES: Path = Path(
    os.getenv("RESIZED_GALLERIES", "/pv/galleries/resized")
).resolve()
EXTENSIONS: List[str] = ["jpg", "jpeg"]
RESIZED_Q: int = 98
RESIZED_SIZE: str = "1600x1200"
THUMB_Q: int = 80
THUMB_SIZE: str = "640x480"


@dataclass(frozen=True)
class ResizeOp:
    src: Path
    dest: Path
    quality: int = RESIZED_Q
    size: str = RESIZED_SIZE

    @property
    def thumb(self) -> "ResizeOp":
        return replace(
            self,
            dest=self.dest.with_suffix(f".thumb{self.dest.suffix}"),
            quality=THUMB_Q,
            size=THUMB_SIZE,
        )

    @property
    def as_convert_args(self) -> List[str]:
        return [
            str(_)
            for _ in [
                self.src,
                "-resize",
                f"{self.size}>",
                "-quality",
                self.quality,
                self.dest,
            ]
        ]


def destinations(image: Path) -> Tuple[ResizeOp, ResizeOp]:
    """ Return a tuple containing the resized image and thumbnail paths.
    """
    rel = image.relative_to(RAW_GALLERIES)
    resize_op = ResizeOp(src=image, dest=RESIZED_GALLERIES / str(rel).lower())

    return resize_op, resize_op.thumb


def resize(op: ResizeOp) -> str:
    # silently ignore the op if the destination file exists
    if op.dest.exists():
        return ""

    debug(op)
    op.dest.parent.mkdir(parents=True, exist_ok=True)
    return str(sh.convert(*op.as_convert_args))


def resize_handler(event: Event) -> Event:
    if event.maskname != "IN_CLOSE_WRITE":
        return event

    event_path = Path(event.pathname)
    if event_path.is_file() and event_path.suffix[1:] in EXTENSIONS:
        for resize_op in destinations(event_path):
            resize(resize_op)


def main():
    """
        1) iterate through raw galleries and make sure all the images
        have been resized + have thumbnails
        2) start a watcher on the RAW_GALLERIES dir and pass new images
        through the same routine
    """
    # Watch for new images being added and resize them accordingly
    thread = Thread(target=start_notifier, args=(RAW_GALLERIES, resize_handler))
    thread.daemon = True
    thread.start()

    # Make sure existing images are processed
    images = multiglob(RAW_GALLERIES, extensions=EXTENSIONS)
    resize_ops = flatmap(destinations, images)

    with Pool() as p:
        p.map(resize, resize_ops)

    while True:
        time.sleep(5)


if __name__ == "__main__":
    main()
