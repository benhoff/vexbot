from vexbot.extensions import develop
from vexbot.extensions import help
from vexbot.extensions import hidden
from vexbot.extensions import intents
from vexbot.extensions import log
# from vexbot.extensions import news
from vexbot.extensions import subprocess


def extension(base,
              alias: list=None,
              name: str=None,
              hidden: bool=False,
              instancemethod=False):

    def wrapper(function):
        new_name = name or function.__name__
        function.command = True
        if instancemethod:
            if hasattr(base, '_commands'):
                pass
            else:
                pass
        else:
            # FIXME: note this doesn't work with the commands
            setattr(base, new_name, function)

        return function

    return wrapper 


def extend(base, function, alias=None, name=None, hidden=False, instancemethod=False):
    extension(base, alias, name, hidden, instancemethod)(function)


def extendmany(base, *functions):
    for function in functions:
        extension(base)(function)
