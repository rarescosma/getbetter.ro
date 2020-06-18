from pathlib import Path
from typing import Any, Callable

import pyinotify as pyinotify
from devtools import debug

from .fs import all_subdirs, is_link_to_dir
from .fun import compose


class WatchManager(pyinotify.WatchManager):
    def deep_watch(self, d: Path) -> None:
        """Return a notifier for handling dir changes"""
        dir_links = [_ for _ in all_subdirs(d) if is_link_to_dir(_)]

        for watch_path in [d, *dir_links]:
            self.add_watch(
                str(watch_path), pyinotify.ALL_EVENTS, rec=True,
            )


class ProcessEvent(pyinotify.ProcessEvent):
    """Calls handler with the changed file path on CLOSE_WRITE"""

    __handler: Callable
    __error_handler: Callable

    def __init__(
        self, handler: Callable, error_handler: Callable, **kargs: Any
    ) -> None:
        self.__handler = handler
        self.__error_handler = error_handler
        super().__init__(**kargs)

    # noinspection PyPep8Naming
    def _process(self, event):
        """Handle CLOSE_WRITE"""
        debug(event)
        try:
            self.__handler(event)
        except Exception as exc:
            self.__error_handler(exc)

    process_IN_CLOSE_WRITE = _process
    process_IN_CREATE = _process


def start_notifier(
    d: Path, handler: Callable = print, error_handler: Callable = print
) -> None:
    wm = WatchManager()
    wm.deep_watch(d)

    def handle_create_dir(event: pyinotify.Event) -> pyinotify.Event:
        event_path = Path(event.pathname)
        if event_path.is_dir() or is_link_to_dir(event_path):
            wm.deep_watch(event_path.resolve())
        return event

    notifier = pyinotify.Notifier(
        wm,
        ProcessEvent(
            handler=compose(handle_create_dir, handler),
            error_handler=error_handler,
        ),
    )

    while True:
        try:
            notifier.process_events()
            if notifier.check_events():
                notifier.read_events()
        except KeyboardInterrupt:
            notifier.stop()
            break
