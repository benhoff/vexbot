import unittest

from vexbot.command_managers import CommandManager


class TestCommandManager(unittest.TestCase):
    def setUp(self):
        messaging = None
        self.command_manager = CommandManager(messaging)

    def test_get_callback_recursively(self):
        pass

    def test_get_callback_recursively_command_none(self):
        """
        since the command is recursive, can expect to pass in `None` as an
        argument
        """
        result = self.command_manager._get_callback_recursively(None)
        self.assertIsNone(result[0])
        self.assertIsNone(result[1])

    def test_get_callback_recursively_callback_none(self):
        """
        want to make sure that if don't pass in a callback, that we get a command

        set a command 'test' with a value of 'blue' and check to see that if we
        pass in that command, we get that value back
        """
        self.command_manager._commands['test'] = 'blue'

        callback = self.command_manager._get_callback_recursively('test')
        self.assertEqual(callback, 'blue')

    def test_get_callback_recursively_callback_is_dict(self):
        """
        since this is a recursive command, want to make sure that that works
        """
        passed_in_dict = {}
        passed_in_dict['test'] = 'blue'

        callback = self.command_manager._get_callback_recursively('test', passed_in_dict)
        self.assertEqual(callback, 'blue')
