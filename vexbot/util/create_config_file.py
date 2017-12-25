from os import path
from configparser import ConfigParser as _ConfigParser

from vexbot import _get_default_port_config
from vexbot.util.get_config_filepath import get_config_filepath as _get_config_filepath


def create_config_file(settings=None):
    filepath = _get_config_filepath()
    if path.isfile(filepath):
        return

    config = _ConfigParser()
    config['vexbot'] = {'kill_on_exit': False,
                        'profile': 'default'}

    config['vexbot_ports'] = _get_default_port_config()

    with open(filepath, 'w') as f:
        config.write(f)
