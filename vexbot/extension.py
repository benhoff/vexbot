def extension(base,
              alias: list=None,
              name: str=None,
              hidden: bool=False,
              instancemethod=False):

    def wrapper(function):
        new_name = name or function.__name__
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
