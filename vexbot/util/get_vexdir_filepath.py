from os import path


def _get_config_dir():
    home_direct = path.expanduser("~")
    config = path.abspath(path.join(home_direct,
                                    '.config'))

    return config


def get_vexdir_filepath():
    vexdir = path.join(_get_config_dir(),
                       'vexbot')

    return vexdir
