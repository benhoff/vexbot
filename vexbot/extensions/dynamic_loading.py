import importlib


def add_extension(self, function_name: str, alias: list=None, call_name: str=None, hidden: bool=False, *args, **kwargs) -> None:
    # split off the last dot as the function name, the rest is the module
    module, function = function_name.rsplit('.', maxsplit=1)
    # strip off any whitespace
    function = function.rstrip()
    # import the module
    module = importlib.import_module(module, package=None)
    # get the function from the module
    function = getattr(module, function)
    self.extend(function, alias=alias, name=call_name, hidden=hidden)

    values = {'function_name': function_name, 'alias': alias, 'call_name': call_name, 'hidden': hidden}

    self._config['extensions'][function_name] = values
    self._config.sync()


def get_extensions(self, *args, **kwargs):
    return tuple(self._config['extensions'].keys())


def remove_extensions(self, function_name: str, *args, **kwargs) -> str:
    popped = self._config['extensions'].pop(function_name)
    return 'Removed: {}'.format(popped)
