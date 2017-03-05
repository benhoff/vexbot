from os import path, mkdir

from vexbot.util.get_vexdir_filepath import get_vexdir_filepath as _get_vexdir_filepath
from vexbot.util.get_vexdir_filepath import _get_config_dir


def create_vexdir():
    config_dir = _get_config_dir()
    vexdir = _get_vexdir_filepath()

    if not path.isdir(config_dir):
        mkdir(config_dir)
    if not path.isdir(vexdir):
        mkdir(vexdir)

    return vexdir
