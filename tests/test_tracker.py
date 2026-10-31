import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'plugin'))

from tracker import Snapshot, Tracker, annots_key  # noqa: E402

A = '/lib/Au/A (1)/A.epub'
B = '/lib/Au/B (2)/B.epub'
KEYS = {annots_key(A): A, annots_key(B): B}
KA, KB = annots_key(A), annots_key(B)


def snap(now, pids=(1,), front=True, idle=1.0, annots=None, hint=A):
    return Snapshot(now, tuple(pids), front, idle, annots or {}, KEYS, hint)


class TrackerTest(unittest.TestCase):
    def setUp(self):
        self.t = Tracker(idle_timeout=300, heartbeat_interval=120)

    def test_start_uses_hint_then_interval_throttle(self):
        hb = self.t.update(snap(1000))
        self.assertEqual((hb.reason, hb.book_path), ('start', A))
        self.assertIsNone(self.t.update(snap(1005)))
        self.assertIsNone(self.t.update(snap(1119)))
        self.assertEqual(self.t.update(snap(1121)).reason, 'interval')

    def test_no_hint_no_page_turn_means_no_guess(self):
        self.assertIsNone(self.t.update(snap(1000, hint=None)))
        hb = self.t.update(snap(1010, hint=None, annots={KB: 1008}))
        self.assertEqual((hb.reason, hb.book_path), ('start', B))

    def test_not_frontmost_or_no_viewer_is_inactive(self):
        self.assertIsNone(self.t.update(snap(1000, front=False)))
        self.assertIsNone(self.t.update(snap(1005, pids=())))
        self.assertFalse(self.t.active)
        self.assertIsNone(self.t.book)

    def test_idle_stops_then_resumes_with_start(self):
        self.t.update(snap(1000))
        self.assertIsNone(self.t.update(snap(1400, idle=400)))
        self.assertFalse(self.t.active)
        self.assertEqual(self.t.update(snap(1500, idle=2)).reason, 'start')

    def test_page_turn_keeps_session_alive_while_input_idle(self):
        self.t.update(snap(1000))
        self.assertEqual(self.t.update(snap(1200, idle=600, annots={KA: 1140})).reason, 'interval')
        self.assertTrue(self.t.active)
        # position save is now 400 s old and input still idle -> session ends
        self.assertIsNone(self.t.update(snap(1540, idle=940, annots={KA: 1140})))
        self.assertFalse(self.t.active)

    def test_idle_unknown_uses_annots_only(self):
        self.assertIsNone(self.t.update(snap(1000, idle=None)))
        self.assertEqual(self.t.update(snap(1001, idle=None, annots={KA: 1000.5})).reason, 'start')

    def test_old_annots_do_not_override_hint(self):
        # B was read yesterday; viewer just launched for A
        hb = self.t.update(snap(1000, annots={KB: 50}))
        self.assertEqual(hb.book_path, A)

    def test_book_switch_on_page_turn_emits_immediately(self):
        self.t.update(snap(1000))
        hb = self.t.update(snap(1010, annots={KB: 1008}))
        self.assertEqual((hb.reason, hb.book_path), ('book', B))

    def test_viewer_relaunch_resets_book(self):
        self.t.update(snap(1000, annots={KB: 1000.5}))
        self.assertEqual(self.t.book, B)
        self.t.update(snap(1010, pids=()))
        hb = self.t.update(snap(1020, pids=(2,), hint=A, annots={KB: 1000.5}))
        self.assertEqual((hb.reason, hb.book_path), ('start', A))

    def test_interval_resets_after_gap(self):
        self.t.update(snap(1000))
        self.t.update(snap(1100, front=False))
        self.assertEqual(self.t.update(snap(1110)).reason, 'start')


if __name__ == '__main__':
    unittest.main()
