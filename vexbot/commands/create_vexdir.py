from os import path, mkdir


def get_vexdir_filepath():
    home_direct = path.expanduser("~")
    vexdir = path.abspath(path.join(home_direct, '.vexbot'))
    return vexdir


def create_vexdir():
    vexdir = get_vexdir_filepath()
    if not path.isdir(vexdir):
        mkdir(vexdir)

    return vexdir
