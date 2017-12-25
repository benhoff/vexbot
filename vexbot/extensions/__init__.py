from vexbot.extension_metadata import extensions as _ext_meta

def extension(base,
              alias: list=None,
              name: str=None,
              hidden: bool=False,
              instancemethod: bool=False,
              roles: list=None,
              short: str=None):

    def wrapper(function):
        # Try to use the meta first
        if short is None and hasattr(function, '_meta'):
            new_short = _ext_meta.get(function._meta, {}).get('short')
        elif short:
            new_short = short
        else:
            new_short = None
        # Then try to use the function name
        if short is None and new_short is None:
            new_short = _ext_meta.get(function.__name__, {}).get('short')

        new_name = name or function.__name__
        function.command = True
        function.hidden = hidden
        function.roles = roles
        function.alias = alias
        function.short = new_short


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
           roles: list=None,
           short: str=None):

    wrapper = extension(base, alias, name, hidden, instancemethod, roles, short)
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
