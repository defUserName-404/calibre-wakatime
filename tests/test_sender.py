import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'plugin'))

from sender import CLI_TIMEOUT, build_command, display_entity  # noqa: E402


class SenderTest(unittest.TestCase):
    def test_command_shape(self):
        cmd = build_command('/cli', 'Title', 'lib', 'learning', 'calibre/9 calibre-wakatime/1', 12.5)
        self.assertEqual(cmd[0], '/cli')
        for flag, val in (('--entity', 'Title'), ('--entity-type', 'app'), ('--category', 'learning'),
                          ('--project', 'lib'), ('--plugin', 'calibre/9 calibre-wakatime/1')):
            self.assertEqual(cmd[cmd.index(flag) + 1], val)
        self.assertEqual(cmd[cmd.index('--time') + 1], '12.500000')

    def test_cli_timeout_set_so_cli_can_queue_offline(self):
        cmd = build_command('/cli', 't', 'p', 'learning', 'ua')
        self.assertEqual(cmd[cmd.index('--timeout') + 1], str(CLI_TIMEOUT))
        self.assertNotIn('--time', cmd)

    def test_hide_titles_is_stable_and_anonymous(self):
        a = display_entity('Secret Book', True)
        self.assertEqual(a, display_entity('Secret Book', True))
        self.assertNotIn('Secret', a)
        self.assertEqual(display_entity('Secret Book', False), 'Secret Book')


if __name__ == '__main__':
    unittest.main()
