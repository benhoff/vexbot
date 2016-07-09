from os import path, mkdir


def create_vexdir():
    home_direct = path.expanduser("~")
    vexdir = path.join(home_direct, '.vexbot')
    if not path.isdir(vexdir):
        mkdir(vexdir)

    return vexdir
