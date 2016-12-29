import logging as _logging

from vexbot.settings_manager import SettingsManager as _SettingsManager
from vexbot.util.create_config_file import create_config_file as _create_config_file
from vexbot.util.create_database import create_database as _create_database


def quickstart():
    _logging.info('Creating Settings Database')
    _create_database()
    settings_manager = _SettingsManager()
    _logging.info('Creating Default Settings')
    settings_manager.create_default()
    _logging.info('Creating Default Config File')
    _create_config_file()
