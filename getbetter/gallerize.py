#!/usr/bin/env python3

import os
import sys
import time
from dataclasses import dataclass, replace
from multiprocessing import Pool
from pathlib import Path
from threading import Thread
from typing import List, Optional, Tuple

import pyinotify
import sh
from devtools import debug

from .fs import multiglob
from .fun import flatmap
from .watch import start_notifier

RAW_GALLERIES: Path = Path(
    os.getenv("RAW_GALLERIES", "/pv/raw_galleries")
).resolve()
RESIZED_GALLERIES: Path = Path(
    os.getenv("RESIZED_GALLERIES", "/pv/content/galleries")
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


def get_resize_ops(image: Path) -> Tuple[ResizeOp, ResizeOp]:
    rel = image.relative_to(RAW_GALLERIES)
    resize_op = ResizeOp(src=image, dest=RESIZED_GALLERIES / str(rel).lower())

    return resize_op, resize_op.thumb


def resize(op: ResizeOp) -> str:
    # silently ignore the op if the destination file exists
    if op.dest.exists():
        return ""

    debug(op)
    op.dest.parent.mkdir(parents=True, exist_ok=True)
    return str(sh.convert(*op.as_convert_args))  # pylint: disable=no-member


def resize_handler(event: pyinotify.Event) -> pyinotify.Event:
    if (resize_path := get_resize_path(event)) is not None:
        for resize_op in get_resize_ops(resize_path):
            resize(resize_op)
    return event


def get_resize_path(event: pyinotify.Event) -> Optional[Path]:
    if event.maskname != "IN_CLOSE_WRITE":
        return None

    event_path = Path(event.pathname)
    return (
        event_path
        if event_path.is_file() and event_path.suffix[1:] in EXTENSIONS
        else None
    )


def main() -> None:
    """
    1) iterate through raw galleries and make sure all the images
    have been resized + have thumbnails
    2) start a watcher on the RAW_GALLERIES dir and pass new images
    through the same routine
    """
    if "-w" in sys.argv[1:]:
        # Watch for new images being added and resize them accordingly
        thread = Thread(
            target=start_notifier, args=(RAW_GALLERIES, resize_handler)
        )
        thread.daemon = True
        thread.start()

    # Make sure existing images are processed
    images = multiglob(RAW_GALLERIES, extensions=EXTENSIONS)
    with Pool() as pool:
        pool.map(resize, flatmap(get_resize_ops, images))

    if "-w" in sys.argv[1:]:
        while True:
            time.sleep(5)


if __name__ == "__main__":
    main()
