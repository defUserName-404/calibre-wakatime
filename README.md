# calibre-wakatime

calibre GUI plugin that sends e-book **reading time** to WakaTime (macOS only).

- Heartbeat: `--entity-type app`, entity = book title, project = library name, category = `learning`.
- Uses the existing `~/.wakatime/wakatime-cli` and `~/.wakatime.cfg` (no API key stored in the plugin).
- Log: `~/.wakatime/calibre-wakatime.log`.

## How it works
The viewer is a separate process with no plugin hooks, so the plugin observes it from outside (every 5 s):
viewer process running (`ps`) + frontmost app (`lsappinfo`) + system idle time (`ioreg`) + the viewer's
`~/Library/Preferences/calibre/viewer/annots/<sha256(book path)>.json` mtimes (written on page turns).
Reading counts while the viewer is frontmost and there was input or a page turn within the idle timeout (default 5 min).
The open book is the last book calibre launched the viewer for, switching to whichever book's annots file is written next.

## Build / install
```sh
./build.sh              # dist/WakaTime.zip
./build.sh --install    # also calibre-customize -a (quit calibre first), then restart calibre
/usr/bin/python3 -m unittest discover -s tests
```
Debug with `calibre-debug -g`.

## Limitations
- Only tracks while the main calibre window is running (the plugin lives there).
- Only books in the calibre library (matched by file path hash).
- Before the first page turn the book is a best guess from calibre's view history.
