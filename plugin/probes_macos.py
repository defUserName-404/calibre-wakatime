"""macOS observation probes. Each returns a safe fallback on any failure; none need special permissions."""
from __future__ import annotations

import os
import re
import subprocess
from typing import Optional

# Viewer app process, whatever the launch route made it look like:
#   .../calibre.app/Contents/MacOS/ebook-viewer                              (direct launch)
#   .../ebook-viewer.app/Contents/MacOS/ebook-viewer-placeholder-for-codesigning  (Finder / Dock)
#   .../ebook-viewer.app/Contents/MacOS/calibre-parallel                     (launched from the calibre GUI)
# The pipe workers nest deeper (ebook-viewer.app/Contents/ebook-edit.app/...) and must not match.
_VIEWER_RE = re.compile(
    r'^\s*(\d+)\s+(?:\S*/calibre\.app/Contents/MacOS/ebook-viewer|\S*/ebook-viewer\.app/Contents/MacOS/[^/\s]+)(?:\s|$)')
_PID_RE = re.compile(r'\bpid\s*=\s*(\d+)')
_IDLE_RE = re.compile(r'"HIDIdleTime"\s*=\s*(\d+)')


def _run(*cmd: str, timeout: float = 3.0) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout
    except Exception:
        return ''


def parse_viewer_pids(ps_output: str) -> tuple:
    pids = []
    for line in ps_output.splitlines():
        m = _VIEWER_RE.match(line)
        if m and '--pipe-worker' not in line:
            pids.append(int(m.group(1)))
    return tuple(pids)


def viewer_pids() -> tuple:
    return parse_viewer_pids(_run('ps', '-axo', 'pid=,command='))


def frontmost_pid() -> Optional[int]:
    asn = _run('lsappinfo', 'front').strip()
    if not asn:
        return None
    m = _PID_RE.search(_run('lsappinfo', 'info', '-only', 'pid', asn))
    return int(m.group(1)) if m else None


def idle_seconds() -> Optional[float]:
    m = _IDLE_RE.search(_run('ioreg', '-c', 'IOHIDSystem', '-d', '4'))
    return int(m.group(1)) / 1e9 if m else None


def annot_mtimes(annots_dir: str) -> dict:
    out = {}
    try:
        with os.scandir(annots_dir) as it:
            for e in it:
                if e.name.endswith('.json'):
                    out[e.name[:-5]] = e.stat().st_mtime
    except OSError:
        pass
    return out
