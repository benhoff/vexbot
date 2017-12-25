from vexbot.extensions import develop
from vexbot.extensions import help
from vexbot.extensions import hidden
from vexbot.extensions import intents
from vexbot.extensions import log
# from vexbot.extensions import news
from vexbot.extensions import subprocess
from vexbot.extensions import admin


def extension(base,
              alias: list=None,
              name: str=None,
              hidden: bool=False,
              instancemethod: bool=False,
              roles: list=None):

    def wrapper(function):
        new_name = name or function.__name__
        function.command = True
        function.hidden = hidden
        function.roles = roles
        function.alias = alias

        if instancemethod:
            # FIXME: implement
            if hasattr(base, '_commands'):
                pass
            else:
                pass
        else:
            setattr(base, new_name, function)

        return function

    return wrapper 


def extend(base,
           function,
           alias: list=None,
           name: str=None,
           hidden: bool=False,
           instancemethod: bool=False,
           roles: list=None):

    wrapper = extension(base, alias, name, hidden, instancemethod, roles)
    wrapper(function)


def extendmany(base,
               *functions,
               hidden: bool=None,
               instancemethod: bool=False,
               roles: list=None):
    for function in functions:
        wrapper = extension(base,
                            hidden=hidden,
                            instancemethod=instancemethod,
                            roles=roles)

        wrapper(function)
