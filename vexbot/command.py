import functools as _functools


def command(function=None,
            alias: list=None,
            hidden: bool=False):

    if function is None:
        return _functools.partial(command,
                                  alias=alias,
                                  hidden=hidden)

    # https://stackoverflow.com/questions/10176226/how-to-pass-extra-arguments-to-python-decorator
    @_functools.wraps(function)
    def wrapper(*args, **kwargs):
        return function(*args, **kwargs)
    # TODO: check for string and convert to list
    if alias is not None:
        wrapper.alias = alias
    wrapper.hidden = hidden
    return wrapper


def extension(base,
              alias: list=None,
              name: str=None,
              hidden: bool=False,
              instancemethod=True):

    def inner(function):
        if instancemethod:
            if hasattr(base, '_commands'):
                pass
            else:
                pass
        else:
            setattr(base, function.__name__, wrapper)

        return function

    return inner
