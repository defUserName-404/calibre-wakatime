# calibre-wakatime

calibre GUI plugin that sends e-book **reading time** to WakaTime (macOS only).

- Heartbeat: `--entity-type app`, entity = book title, project = library name, category = `learning`.
- Uses the existing `~/.wakatime/wakatime-cli` and `~/.wakatime.cfg` (no API key stored in the plugin).
- Log: `~/.wakatime/calibre-wakatime.log` (also records when the viewer is detected/lost and which book is open, so a silent "not tracking" shows up there).

## Install
Requirements: macOS, calibre 6+ (tested on 9.17.0), and `wakatime-cli` with your API key. Any WakaTime
editor plugin installs the CLI to `~/.wakatime/`; the key lives in `~/.wakatime.cfg`.

1. Download `WakaTime.zip` from the [latest release](https://github.com/defUserName-404/calibre-wakatime/releases/latest).
2. In calibre: Preferences → Plugins → **Load plugin from file**, pick the zip, restart calibre.
   (Or quit calibre and run `calibre-customize -a WakaTime.zip`.)
3. If no WakaTime button shows, add it under Preferences → Toolbars & menus.
4. Read a book in the calibre viewer, then check `~/.wakatime/calibre-wakatime.log` and your WakaTime dashboard
   (app entity = book title, project = library, category *Learning*).

Settings (idle timeout, category, project name, hide titles, CLI path): Preferences → Plugins → WakaTime → Customize.

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
- macOS only; the toolbar menu and settings dialog are covered by code-level checks, not click-through testing.

## License
[MIT](LICENSE)
