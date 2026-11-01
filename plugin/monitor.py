"""Background polling thread: probes -> Tracker -> Sender. Calibre-specific lookups are injected."""
from __future__ import annotations

import threading
import time

from calibre_plugins.wakatime import probes_macos as probes
from calibre_plugins.wakatime.sender import log
from calibre_plugins.wakatime.tracker import Snapshot, Tracker, viewer_state

POLL_SECONDS = 5.0


class Monitor(threading.Thread):
    """lookup: object with key_paths(keys) -> dict, hint_path() -> str|None, describe(path) -> (title, library)|None."""

    def __init__(self, get_cfg, annots_dir, lookup, sender):
        super().__init__(daemon=True, name='wakatime-monitor')
        self._get_cfg = get_cfg
        self._annots_dir = annots_dir
        self._lookup = lookup
        self._sender = sender
        self._stop_evt = threading.Event()
        self.paused = False
        self.tracker = Tracker()
        self._last_state = None

    def stop(self) -> None:
        self._stop_evt.set()

    def apply_settings(self) -> None:
        cfg = self._get_cfg()
        self.tracker.idle_timeout = cfg['idle_timeout_min'] * 60.0
        self.tracker.heartbeat_interval = float(cfg['heartbeat_interval_s'])

    def _snapshot(self) -> Snapshot:
        now = time.time()
        pids = probes.viewer_pids()
        if not pids:
            return Snapshot(now)
        mtimes = probes.annot_mtimes(self._annots_dir)
        return Snapshot(
            now=now, viewer_pids=pids,
            viewer_frontmost=probes.frontmost_pid() in pids,
            idle_s=probes.idle_seconds(), annot_mtimes=mtimes,
            key_paths=self._lookup.key_paths(mtimes), hint_path=self._lookup.hint_path())

    def run(self) -> None:
        self.apply_settings()
        log('monitor started')
        while not self._stop_evt.wait(POLL_SECONDS):
            try:
                if self.paused or not self._get_cfg()['enabled']:
                    self.tracker.update(Snapshot(time.time()))
                    continue
                snap = self._snapshot()
                hb = self.tracker.update(snap)
                state = viewer_state(snap, self.tracker.book)
                if state != self._last_state:
                    log(state)
                    self._last_state = state
                if hb:
                    info = self._lookup.describe(hb.book_path)
                    if info:
                        title, library = info
                        cfg = self._get_cfg()
                        project = cfg['fixed_project'] if cfg['project_mode'] == 'fixed' and cfg['fixed_project'] else library
                        self._sender.send(title, project, hb.time)
                    else:
                        log(f'could not describe {hb.book_path}')
            except Exception as e:  # never let the thread die
                log(f'monitor error: {e!r}')
        log('monitor stopped')
