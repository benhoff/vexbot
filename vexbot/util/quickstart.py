from vexbot.util.create_database import create_database as _create_database
from vexbot.settings_manager import SettingsManager as _SettingsManager


def quickstart():
    _create_database()
    settings_manager = _SettingsManager()
    default_settings = {'context': 'default',
            'name': 'vexbot',
            'subscribe_address': 'tcp://127.0.0.1:4000',
            'publish_address': 'tcp://127.0.0.1:4001',
            'monitor_address': '',}


    settings_manager.create_robot_settings(default_settings)
