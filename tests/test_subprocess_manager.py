import unittest

from vexbot.subprocess_manager import SubprocessManager


class TestSubprocessManager(unittest.TestCase):
    def setUp(self):
        self.subprocess_manager = SubprocessManager()
        # register a subprocess? With a name?

    def test_registered_subprocesses(self):
        test_obj = object()
        self.subprocess_manager.register('test', test_obj)
        registered = self.subprocess_manager.registered_subprocesses()
        self.assertIn('test', registered)

    def test_register_with_blacklist(self):
        blacklisted = 'black'
        self.subprocess_manager.blacklist.append(blacklisted)
        self.subprocess_manager.register(blacklisted, None)
        registered = self.subprocess_manager.registered_subprocesses()
        self.assertNotIn(blacklisted, registered)

    def test_update_setting_value(self):
        self.subprocess_manager.update_settings('test', {'test_value': 'old'})
        self.subprocess_manager.update_setting_value('test',
                                                     'test_value',
                                                     'new')

        result = self.subprocess_manager.get_settings('test')
        self.assertEqual(result['test_value'], 'new')
        self.assertNotEqual(result['test_value'], 'old')

    def test_update_setting(self):
        settings = {'setting': 'value'}
        self.subprocess_manager.update_settings('test', settings)
        gotten_settings = self.subprocess_manager.get_settings('test')
        self.assertEqual(settings, gotten_settings)
