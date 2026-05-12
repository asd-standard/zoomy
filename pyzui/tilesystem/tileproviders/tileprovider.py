## PyZUI - Python Zooming User Interface
## Copyright (C) 2009 David Roberts <d@vidr.cc>
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License
## as published by the Free Software Foundation; either version 3
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, see <https://www.gnu.org/licenses/>.

"""Threaded class for loading tiles into memory (abstract base class)."""

from collections import deque
from threading import Condition, Event, Thread
from typing import TYPE_CHECKING, Any

from pyzui.logger import get_logger
from pyzui.tilesystem.tile import Tile

if TYPE_CHECKING:
    from pyzui.tilesystem.tilestore.tilecache import TileCache

TileID = tuple[str, int, int, int]


class TileProvider(Thread):
    """
    Constructor :
        TileProvider(tilecache)
    Parameters :
        tilecache : TileCache

    TileProvider(tilecache) --> TileProvider

    `TileProvider` objects are used for loading tiles into TileCache objects.

    This is an abstract base class that provides threaded infrastructure for
    loading tiles into memory. Subclasses must implement the `_load` method
    to define how tiles are actually loaded.

    Requests are processed in LIFO (Last In First Out) order.
    """

    def __init__(self, tilecache: "TileCache") -> None:
        """
        Method :
            TileProvider.__init__(tilecache)
        Parameters :
            tilecache : TileCache

        TileProvider.__init__(tilecache) --> None

        Create a new TileProvider for loading tiles into the given `tilecache`.

        Initializes the thread infrastructure, task queue, and logger for this
        tile provider instance.
        """
        Thread.__init__(self)
        self.daemon = True

        self.__tilecache = tilecache

        self.__tasks: deque[TileID] = deque()
        self.__tasks_available = Condition()

        # Pause/resume mechanism
        self.__pause_event = Event()
        self.__pause_event.set()  # Start in running (not paused) state

        # Shutdown event to signal the thread to stop
        self.__shutdown_event = Event()

        self._logger = get_logger(str(self))

    def stop(self) -> None:
        """Signal the tile provider thread to stop and wake it if blocked."""
        self.__shutdown_event.set()
        self.__pause_event.set()
        try:
            self.__tasks_available.acquire()
            self.__tasks_available.notify()
        finally:
            self.__tasks_available.release()

    def request(self, tile_id: TileID) -> None:
        """
        Method :
            TileProvider.request(tile_id)
        Parameters :
            tile_id : Tuple[str, int, int, int]

        TileProvider.request(tile_id) --> None

        Request the tile identified by `tile_id` be loaded into the
        tilecache.

        Requests are processed in a LIFO order.

        If the tile is unavailable, then None will be inserted into the
        tilecache to indicate this.
        """
        self.__tasks_available.acquire()
        self.__tasks.append(tile_id)
        self.__tasks_available.notify()
        self.__tasks_available.release()

    def _load(self, tile_id: TileID) -> Any | None:
        """
        Method :
            TileProvider._load(tile_id)
        Parameters :
            tile_id : Tuple[str, int, int, int]

        TileProvider._load(tile_id) --> Image or None

        Load the requested tile, and return it as an `Image` object.

        Returns None if the tile does not exist.
        """
        pass

    def run(self) -> None:
        """
        Method :
            TileProvider.run()
        Parameters :
            None

        TileProvider.run() --> None

        Run a loop to load requested tiles.
        """
        while not self.__shutdown_event.is_set():
            self.__pause_event.wait()
            if self.__shutdown_event.is_set():
                break

            self.__tasks_available.acquire()
            while not self.__tasks and not self.__shutdown_event.is_set():
                self.__tasks_available.wait()
            if self.__shutdown_event.is_set():
                self.__tasks_available.release()
                break
            tile_id = self.__tasks.pop()
            self.__tasks_available.release()

            self.__pause_event.wait()
            if self.__shutdown_event.is_set():
                break

            if tile_id not in self.__tilecache:
                try:
                    tile = self._load(tile_id)
                except Exception:
                    self._logger.exception("error loading tile")
                    tile = None

                if tile:
                    self._logger.debug("loaded %s", str(tile_id))
                    self.__tilecache[tile_id] = Tile(tile)

                    del tile
                else:
                    self._logger.debug("unavailable %s", str(tile_id))
                    self.__tilecache[tile_id] = None

    def purge(self, media_id: str | None = None) -> None:
        """
        Method :
            TileProvider.purge(media_id)
        Parameters :
            media_id : Optional[str]

        TileProvider.purge(media_id) --> None

        Purge all tasks for the given `media_id`. All tasks will be purged
        if `media_id` is omitted.
        """
        self.__tasks_available.acquire()
        self._logger.debug("purging %s", media_id or "all")
        if media_id:
            new_tasks: deque[TileID] = deque()
            for task in self.__tasks:
                if task[0] != media_id:
                    new_tasks.append(task)
            self.__tasks = new_tasks
        else:
            self.__tasks = deque()
        self.__tasks_available.release()

    def pause(self) -> None:
        """
        Method :
            TileProvider.pause()
        Parameters :
            None

        TileProvider.pause() --> None

        Pause the tile provider thread. The thread will stop processing
        new tasks until resume() is called.
        """
        self._logger.debug("pausing")
        self.__pause_event.clear()

    def resume(self) -> None:
        """
        Method :
            TileProvider.resume()
        Parameters :
            None

        TileProvider.resume() --> None

        Resume the tile provider thread after it was paused.
        """
        self._logger.debug("resuming")
        self.__pause_event.set()

    def __str__(self) -> str:
        """
        Method :
            TileProvider.__str__()
        Parameters :
            None

        TileProvider.__str__() --> str

        Return a human-readable string representation of the TileProvider.
        """
        return type(self).__name__

    def __repr__(self) -> str:
        """
        Method :
            TileProvider.__repr__()
        Parameters :
            None

        TileProvider.__repr__() --> str

        Return a formal string representation of the TileProvider.
        """
        return f"{type(self).__name__}()"
