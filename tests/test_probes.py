import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'plugin'))

from probes_macos import parse_viewer_pids  # noqa: E402

APP = '/Applications/calibre.app/Contents'
PS = '\n'.join([
    f'  100 {APP}/MacOS/calibre --with-library /x',
    f'  101 {APP}/ebook-viewer.app/Contents/ebook-edit.app/Contents/headless.app/Contents/MacOS/calibre-parallel --pipe-worker from calibre.utils.ipc.pool import run_main',
    f'  102 {APP}/ebook-viewer.app/Contents/MacOS/calibre-parallel',  # viewer launched from the calibre GUI
    f'  103 {APP}/ebook-viewer.app/Contents/MacOS/ebook-viewer-placeholder-for-codesigning',  # Finder launch
    f'  104 {APP}/MacOS/ebook-viewer --raise-window --new-instance /tmp/My Books/a b.epub',  # direct launch
    f'  105 {APP}/ebook-viewer.app/Contents/MacOS/calibre-parallel --pipe-worker from x import y',  # worker in viewer bundle
    f'  106 {APP}/MacOS/ebook-edit /tmp/a.epub',
])


class ProbeTest(unittest.TestCase):
    def test_matches_every_viewer_launch_route_but_not_workers(self):
        self.assertEqual(parse_viewer_pids(PS), (102, 103, 104))

    def test_empty(self):
        self.assertEqual(parse_viewer_pids(''), ())


if __name__ == '__main__':
    unittest.main()
