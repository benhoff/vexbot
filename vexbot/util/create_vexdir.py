from os import path, mkdir


def _get_config_dir():
    home_direct = path.expanduser("~")
    config = path.abspath(path.join(home_direct,
                                    '.config'))

    return config

def get_vexdir_filepath():
    vexdir = path.join(_get_config_dir(),
                       'vexbot')

    return vexdir


def create_vexdir():
    config_dir = _get_config_dir()
    vexdir = get_vexdir_filepath()

    if not path.isdir(config_dir):
        mkdir(config_dir)
    if not path.isdir(vexdir):
        mkdir(vexdir)

    return vexdir
