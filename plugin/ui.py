import hashlib
import os
import re
import threading
import time

from qt.core import QMenu, pyqtSignal

from calibre.constants import config_dir
from calibre.gui2 import info_dialog
from calibre.gui2.actions import InterfaceAction

from calibre_plugins.wakatime.config import get_cfg, prefs
from calibre_plugins.wakatime.monitor import Monitor
from calibre_plugins.wakatime.sender import Sender, log

PLUGIN_VERSION = '1.0.0'
_ID_RE = re.compile(r'\((\d+)\)$')


class Lookup:
    """Maps viewer annotation keys to library books. Runs in the monitor thread; uses the thread-safe new_api."""

    def __init__(self, gui):
        self.gui = gui
        self._known = {}  # sha256(path) -> path
        self._lib = None
        self._misses = {}  # key -> time of last failed scan
        self._last_scan = 0.0

    def _db(self):
        return self.gui.current_db.new_api

    def _scan(self, db):
        known = {}
        for book_id in db.all_book_ids():
            for fmt in db.formats(book_id):
                p = db.format_abspath(book_id, fmt)
                if p:
                    known[hashlib.sha256(p.encode('utf-8')).hexdigest()] = p
        self._known = known
        self._last_scan = time.time()

    def key_paths(self, mtimes):
        db = self._db()
        if db is not self._lib:  # library switched
            self._lib, self._known, self._misses = db, {}, {}
        # rescan only for keys modified recently that we don't know yet, at most once a minute
        recent = [k for k, m in mtimes.items() if time.time() - m < 600 and k not in self._known]
        if recent and time.time() - self._last_scan > 60:
            self._scan(db)
        return {k: self._known[k] for k in mtimes if k in self._known}

    def hint_path(self):
        # book id of the last book calibre launched the viewer for; format picked via the viewer's own annots later
        try:
            hist = self._db().pref('gui_view_history') or []
            book_id, fmt = hist[0][0], hist[0][1]
            return self._db().format_abspath(book_id, fmt)
        except Exception as e:
            log(f'hint unavailable: {e!r}')
            return None

    def describe(self, path):
        db = self._db()
        m = _ID_RE.search(os.path.basename(os.path.dirname(path)))
        title = db.field_for('title', int(m.group(1))) if m else None
        if not title:
            title = os.path.splitext(os.path.basename(path))[0]
        return title, os.path.basename(db.backend.library_path.rstrip('/'))


class WakaTimeAction(InterfaceAction):
    name = 'WakaTime'
    action_spec = ('WakaTime', None, 'Track e-book reading time in WakaTime', None)
    action_type = 'current'
    action_add_menu = True
    popup_type = 2  # QToolButton.InstantPopup

    today_ready = pyqtSignal(str)

    def genesis(self):
        icon = get_icons('images/icon.png', 'WakaTime')
        self.qaction.setIcon(icon)
        self.menu = QMenu(self.gui)
        self.qaction.setMenu(self.menu)

        self.pause_action = self.create_menu_action(
            self.menu, 'wakatime_pause', 'Pause tracking', description='Pause or resume tracking')
        self.pause_action.setCheckable(True)
        self.pause_action.toggled.connect(self._toggle_pause)
        self.create_menu_action(self.menu, 'wakatime_today', "Today's time…", triggered=self._show_today)
        self.menu.addSeparator()
        self.create_menu_action(self.menu, 'wakatime_settings', 'Settings…', triggered=self._settings)

        self.today_ready.connect(lambda text: info_dialog(
            self.gui, 'WakaTime', text or 'No data (is wakatime-cli installed?)', show=True))
        self.sender = Sender(get_cfg, f'calibre/{self._calibre_version()} calibre-wakatime/{PLUGIN_VERSION}')
        self.monitor = None

    @staticmethod
    def _calibre_version():
        from calibre.constants import numeric_version
        return '.'.join(map(str, numeric_version))

    def initialization_complete(self):
        annots_dir = os.path.join(config_dir, 'viewer', 'annots')
        self.monitor = Monitor(get_cfg, annots_dir, Lookup(self.gui), self.sender)
        self.monitor.start()

    def shutting_down(self):
        if self.monitor:
            self.monitor.stop()

    def apply_settings(self):
        if self.monitor:
            self.monitor.apply_settings()

    def _toggle_pause(self, paused):
        if self.monitor:
            self.monitor.paused = paused
        self.pause_action.setText('Resume tracking' if paused else 'Pause tracking')

    def _show_today(self):
        threading.Thread(
            target=lambda: self.today_ready.emit(self.sender.run_cli('--today')), daemon=True).start()

    def _settings(self):
        self.interface_action_base_plugin.do_user_config(self.gui)
