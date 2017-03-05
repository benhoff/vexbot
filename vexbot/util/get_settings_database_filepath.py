from os import path

from vexbot.util.get_vexdir_filepath import get_vexdir_filepath as _get_vexdir_filpath


def get_settings_database_filepath():
    vexdir = _get_vexdir_filpath()
    settings_filepath = path.join(vexdir, 'settings.sqlite3')
    return settings_filepath
