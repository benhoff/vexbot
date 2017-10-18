from os import path

from vexbot.util.get_vexdir_filepath import get_vexdir_filepath


def get_certificate_filepath():
    vexdir = get_vexdir_filepath()
    certs = path.join(vexdir, 'certificates')
    return certs
