"""wakatime-cli discovery and heartbeat delivery (worker thread; never raises into the caller)."""
from __future__ import annotations

import hashlib
import os
import platform
import queue
import subprocess
import threading
import time
from typing import Optional

LOG_PATH = os.path.expanduser('~/.wakatime/calibre-wakatime.log')


def log(msg: str) -> None:
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        if os.path.exists(LOG_PATH) and os.path.getsize(LOG_PATH) > 512 * 1024:
            os.replace(LOG_PATH, LOG_PATH + '.1')
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(time.strftime('%Y-%m-%d %H:%M:%S ') + msg + '\n')
    except OSError:
        pass


def find_cli(override: str = '') -> Optional[str]:
    arch = 'arm64' if platform.machine() == 'arm64' else 'amd64'
    home = os.path.expanduser('~/.wakatime')
    for p in (override, os.path.join(home, 'wakatime-cli'), os.path.join(home, f'wakatime-cli-darwin-{arch}')):
        if p and os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return None


def build_command(cli: str, entity: str, project: str, category: str, plugin_ua: str,
                  ts: Optional[float] = None) -> list:
    cmd = [cli, '--entity', entity, '--entity-type', 'app', '--category', category,
           '--project', project, '--plugin', plugin_ua]
    if ts is not None:
        cmd += ['--time', f'{ts:.6f}']
    return cmd


def display_entity(title: str, hide: bool) -> str:
    if not hide:
        return title
    return 'Book ' + hashlib.sha256(title.encode('utf-8')).hexdigest()[:8]


class Sender:
    def __init__(self, get_cfg, plugin_ua: str):
        self._get_cfg = get_cfg
        self._ua = plugin_ua
        self._q: queue.Queue = queue.Queue(maxsize=100)
        self._warned = False
        threading.Thread(target=self._run, daemon=True, name='wakatime-sender').start()

    def send(self, title: str, project: str, ts: float) -> None:
        try:
            self._q.put_nowait((title, project, ts))
        except queue.Full:
            log('queue full, dropping heartbeat')

    def run_cli(self, *args: str, timeout: float = 15.0) -> str:
        cli = find_cli(self._get_cfg()['cli_path'])
        if not cli:
            return ''
        try:
            r = subprocess.run([cli, *args], capture_output=True, text=True, timeout=timeout)
            return (r.stdout or r.stderr).strip()
        except Exception as e:
            log(f'cli error: {e}')
            return ''

    def _run(self) -> None:
        while True:
            title, project, ts = self._q.get()
            try:
                cfg = self._get_cfg()
                cli = find_cli(cfg['cli_path'])
                if not cli:
                    if not self._warned:
                        log('wakatime-cli not found in ~/.wakatime; install WakaTime or set the CLI path in settings')
                        self._warned = True
                    continue
                entity = display_entity(title, cfg['hide_titles'])
                cmd = build_command(cli, entity, project, cfg['category'], self._ua, ts)
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                log(f'heartbeat entity={entity!r} project={project!r} rc={r.returncode}'
                    + (f' err={r.stderr.strip()[:200]!r}' if r.returncode else ''))
            except Exception as e:
                log(f'send failed: {e}')
