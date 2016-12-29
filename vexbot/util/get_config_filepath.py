from os import path

from vexbot.util.get_vexdir_filepath import get_vexdir_filepath as _get_vexdir_filepath


def get_config_filepath():
    vexdir = _get_vexdir_filepath()
    config_filepath = path.join(vexdir, 'config.ini')
    return config_filepath

