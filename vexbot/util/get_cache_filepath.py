from os import path


def get_cache_filepath() -> str:
    home_direct = path.expanduser("~")
    cache = path.abspath(path.join(home_direct,
                                   '.cache'))
    cache = path.join(cache, 'vexbot')
    return cache


def get_cache(name: str) -> str:
    filepath = get_cache_filepath()
    filepath = path.join(filepath, name)
    return filepath
