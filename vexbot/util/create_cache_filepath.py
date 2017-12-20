from os import path, mkdir
from vexbot.util.get_cache_filepath import get_cache_filepath


def create_cache_directory():
    home_direct = path.expanduser("~")
    cache = path.abspath(path.join(home_direct,
                                   '.cache'))

    if not path.isdir(cache):
        mkdir(cache)
    cache = path.join(cache, 'vexbot')
    if not path.isdir(cache):
        mkdir(cache)

