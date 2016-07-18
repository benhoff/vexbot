import unittest
import vexmessage
from vexbot.command_managers import (AdapterCommandManager,
                                     BotCommandManager,
                                     CommandManager)

from vexbot.subprocess_manager import SubprocessManager


class Message:
    def __init__(self):
        self.response = None
        self.status = None
        self.commands = None

    def send_response(self, *args, **kwargs):
        self.response = (args, kwargs)

    def send_status(self, status):
        self.status = status

    def send_command(self, *args, **kwargs):
        self.commands = [args, kwargs]


class MockRobot:
    def __init__(self):
        self.messaging = Message()
        self.subprocess_manager = SubprocessManager()


class TestCommandManager(unittest.TestCase):
    def setUp(self):
        self.command_manager = CommandManager(Message())

    def test_register_command(self):
        def _test():
            pass

        test_dict = {'blah': _test}
        self.command_manager.register_command('test', test_dict)
        self.assertIn('test', self.command_manager._commands)
        self.assertFalse(self.command_manager.is_command('test'))
        self.assertFalse(self.command_manager.is_command('blah'))
        self.command_manager.register_command('blah', _test)
        self.assertTrue(self.command_manager.is_command('blah'))
        # FIXME: ?
        self.assertTrue(self.command_manager.is_command('test blah'))

    def test_help(self):
        message = vexmessage.Message('target', 'source', 'CMD', command='help')
        self.command_manager.parse_commands(message)
        response_sent = self.command_manager._messaging.response[1]
        self.assertIn('response', response_sent)
        message = vexmessage.Message('target',
                                     'source',
                                     'CMD',
                                     command='help commands')

        self.command_manager.parse_commands(message)
        response_sent = self.command_manager._messaging.response[1]['response']
        self.assertIn('help', response_sent)
        self.assertIn('commands', response_sent)

    def test_help_specific(self):
        message = vexmessage.Message('target',
                                     'source',
                                     'CMD',
                                     command='help',
                                     args=['commands'])

        self.command_manager.parse_commands(message)
        response = self.command_manager._messaging.response
        self.assertIsNotNone(response)

    def test_commands(self):
        message = vexmessage.Message('target',
                                     'source',
                                     'CMD',
                                     command='commands')

        self.command_manager.parse_commands(message)
        response_sent = self.command_manager._messaging.response
        answer = response_sent[1]['response']
        self.assertIn('commands', answer)
        self.assertIn('help', answer)

    def test_is_command_with_call(self):

        def t(*args):
            pass

        self.command_manager.register_command('t', t)
        called = self.command_manager.is_command('t', True)
        self.assertTrue(called)
        not_called = self.command_manager.is_command('f', True)
        self.assertFalse(not_called)
        # FIXME: not sure what actually want here
        called_w_args = self.command_manager.is_command('t these are args',
                                                        True)

        self.assertTrue(called_w_args)

    def test_get_callback_recursively_none(self):
        result = self.command_manager._get_callback_recursively(None)
        self.assertEqual(len(result), 3)
        for r in result:
            self.assertIsNone(r)

    def test_cmd_commands(self):
        def t():
            pass
        self.command_manager.register_command('test', t)
        nested = {'test': t}
        self.command_manager.register_command('nested', nested)
        commands = self.command_manager._cmd_commands(None)
        self.assertIn('test', commands)
        self.assertIn('nested test', commands)
        self.assertNotIn('blah', commands)
        # TODO: test `help` and `commands`?
        self.assertEqual(len(commands), 4)


class MockProcess:
    def __init__(self):
        self.killed = False

    def poll(self):
        return None

    def terminate(self):
        pass

    def kill(self):
        self.killed = True


class TestBotCommandManager(unittest.TestCase):
    def setUp(self):
        robot = MockRobot()
        self.command_manager = BotCommandManager(robot)
        self.command_manager._messaging = Message()
        self.subprocess_manager = robot.subprocess_manager
        self.messaging = self.command_manager._messaging

    def test_settings(self):
        message = vexmessage.Message('target',
                                     'source',
                                     'CMD',
                                     command='subprocess',
                                     args='settings test',
                                     parsed_args=['test', ])

        self.subprocess_manager.update_settings('test',
                                                {'value': 'test_value'})

        self.command_manager.parse_commands(message)
        response = self.messaging.response[1]['response']
        self.assertIn('value', response)

    def test_kill(self):
        mock = MockProcess()
        self.subprocess_manager._subprocess['test'] = mock
        message = vexmessage.Message('target',
                                     'source',
                                     'CMD',
                                     command='kill test')

        self.command_manager.parse_commands(message)
        self.assertTrue(mock.killed)

    def test_killall(self):
        def _mock_kill(*args, **kwargs):
            # due to scope issues, it's easiest to just tack on to the original
            # message to show that it was called correctly
            args[0].contents['killed'] = True

        self.subprocess_manager.killall = _mock_kill
        self.command_manager._commands['killall'] = _mock_kill

        message = vexmessage.Message('target',
                                     'source',
                                     'CMD',
                                     command='killall')

        self.command_manager.parse_commands(message)
        self.assertTrue(message.contents.get('killed'))

    def test_restart_bot(self):
        pass
        """
        message = vexmessage.Message('target',
                                     'source',
                                     'CMD',
                                     command='restart_bot')

        with self.assertRaises(SystemExit):
            self.command_manager.parse_commands(message)
        """

    def test_alive(self):
        self.subprocess_manager.register('test2', object())
        message = vexmessage.Message('tgt', 'source', 'CMD', command='alive')
        self.command_manager.parse_commands(message)
        commands = self.messaging.commands
        self.assertEqual(commands[1].get('command'), 'alive')

    def test_start(self):
        # TODO: finish
        message = vexmessage.Message('tgt', 'source', 'CMD', command='start')
        self.command_manager.parse_commands(message)

    def test_subprocesses(self):
        self.subprocess_manager.register('test', object())
        message = vexmessage.Message('tgt',
                                     'source',
                                     'CMD',
                                     command='subprocesses')

        self.command_manager.parse_commands(message)
        response = self.command_manager._messaging.response[1]['response']
        self.assertIn('test', response)

    def test_restart(self):
        # TODO: finish
        message = vexmessage.Message('tgt', 'source', 'CMD', command='restart')
        self.command_manager.parse_commands(message)

    def test_terminate(self):
        # TODO: finish
        message = vexmessage.Message('target',
                                     'source',
                                     'CMD',
                                     command='terminate')

        self.command_manager.parse_commands(message)

    def test_running(self):

        self.subprocess_manager._subprocess['test'] = MockProcess()
        message = vexmessage.Message('tgt', 'source', 'CMD', command='running')
        self.command_manager.parse_commands(message)
        response = self.command_manager._messaging.response[1]['response']
        self.assertIn('test', response)


class TestAdapapterCommandManager(unittest.TestCase):
    def setUp(self):
        self.command_manager = AdapterCommandManager(Message())

    def test_alive(self):
        messaging = self.command_manager._messaging

        self.command_manager._alive()
        self.assertIsNotNone(messaging.status)
        self.assertEqual(messaging.status, 'CONNECTED')
