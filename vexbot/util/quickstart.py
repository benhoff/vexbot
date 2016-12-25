from vexbot.util.create_database import create_database as _create_database
from vexbot.settings_manager import SettingsManager as _SettingsManager


def quickstart():
    _create_database()
    settings_manager = _SettingsManager()
    settings_manager.create_default()
