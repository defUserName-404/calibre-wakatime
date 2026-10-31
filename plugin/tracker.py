"""Pure reading-session state machine. No Qt, no subprocess, no calibre imports."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Optional


def annots_key(path: str) -> str:
    """Name (sans .json) of the viewer's per-book annotations file."""
    return hashlib.sha256(path.encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class Snapshot:
    now: float
    viewer_pids: tuple = ()  # pids of running ebook-viewer processes
    viewer_frontmost: bool = False
    idle_s: Optional[float] = None  # seconds since last HID input; None if unknown
    annot_mtimes: dict = field(default_factory=dict)  # annots key -> mtime
    key_paths: dict = field(default_factory=dict)  # annots key -> library book path (resolved by caller)
    hint_path: Optional[str] = None  # book calibre last launched the viewer for


@dataclass(frozen=True)
class Heartbeat:
    book_path: str
    time: float
    reason: str  # 'start' | 'book' | 'interval'


class Tracker:
    def __init__(self, idle_timeout: float = 300.0, heartbeat_interval: float = 120.0):
        self.idle_timeout = idle_timeout
        self.heartbeat_interval = heartbeat_interval
        self.active = False
        self.book: Optional[str] = None
        self._pids: frozenset = frozenset()
        self._floor = 0.0  # annots written before this predate the current viewer session
        self._last_sent: Optional[float] = None

    def _track_book(self, snap: Snapshot) -> None:
        pids = frozenset(snap.viewer_pids)
        if not pids:
            self.book = None
        elif pids - self._pids:
            # viewer (re)launched: start from calibre's last-opened book, refine on first page turn
            self._floor = snap.now
            self.book = snap.hint_path
        self._pids = pids
        if not pids:
            return
        fresh = [(m, snap.key_paths[k]) for k, m in snap.annot_mtimes.items()
                 if m > self._floor and k in snap.key_paths]
        if fresh:
            self.book = max(fresh)[1]

    def _last_activity(self, snap: Snapshot, book: str) -> Optional[float]:
        times = []
        if snap.idle_s is not None:
            times.append(snap.now - snap.idle_s)
        mtime = snap.annot_mtimes.get(annots_key(book))
        if mtime is not None:
            times.append(mtime)
        return max(times) if times else None

    def update(self, snap: Snapshot) -> Optional[Heartbeat]:
        prev_book = self.book
        self._track_book(snap)
        book = self.book if snap.viewer_frontmost else None
        last = self._last_activity(snap, book) if book else None
        active = last is not None and (snap.now - last) < self.idle_timeout

        hb = None
        if active:
            if not self.active:
                reason = 'start'
            elif book != prev_book:
                reason = 'book'
            elif self._last_sent is None or snap.now - self._last_sent >= self.heartbeat_interval:
                reason = 'interval'
            else:
                reason = None
            if reason:
                hb = Heartbeat(book, snap.now, reason)
                self._last_sent = snap.now
        else:
            self._last_sent = None
        self.active = active
        return hb
