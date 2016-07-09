import unittest

from vexbot.command_managers import CommandManager


class TestCommandManager(unittest.TestCase):
    def setUp(self):
        messaging = None
        self.command_manager = CommandManager(messaging)

    def test_get_callback_recursively_command_none(self):
        """
        since the command is recursive, can expect to pass in `None` as an
        argument
        """
        result = self.command_manager._get_callback_recursively(None)
        self.assertIsNone(result[0])
        self.assertIsNone(result[1])
        self.assertIsNone(result[2])

    def test_get_callback_recursively_callback_none(self):
        """
        want to make sure that if don't pass in a callback, that we get a
        command

        set a command 'test' with a value of 'blue' and check to see that if we
        pass in that command, we get that value back
        """
        def _test():
            pass

        self.command_manager._commands['test'] = _test

        get_callback = self.command_manager._get_callback_recursively

        callback, command, args = get_callback('test')
        self.assertEqual(callback, _test)
        self.assertEqual(command, 'test')

    def test_get_callback_recursively_callback_is_dict(self):
        """
        since this is a recursive command, want to make sure that that works
        """
        self.command_manager.register_command('test', 'blue')
        get_callback = self.command_manager._get_callback_recursively

        with self.assertRaises(TypeError):
            get_callback('test', ['trigger', ])
        # self.assertEqual(callback, 'blue')

    def test_get_callback_args(self):
        def _test():
            pass
        self.command_manager.register_command('subprocess',
                                              {'settings': _test})

        command = 'subprocess'
        args = ['settings', 'irc']
        get_callback = self.command_manager._get_callback_recursively
        callback, command_string, args = get_callback(command, args)
        self.assertEqual(args[0], 'irc')

if __name__ == '__main__':
    unittest.main()
