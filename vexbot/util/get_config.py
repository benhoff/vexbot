from configparser import ConfigParser as _ConfigParser

from vexbot.util.get_config_filepath import get_config_filepath as _get_config_filepath


def get_config(filepath=None):
    if filepath is None:
        filepath = _get_config_filepath()
    config = _ConfigParser()
    config.read(filepath)
    config_dict = {s: dict(config.items(s))
                   for s
                   in config.sections()}

    return config_dict
