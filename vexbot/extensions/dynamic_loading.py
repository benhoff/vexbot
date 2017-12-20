import importlib


def add_extension(self, function_name: str, alias: list=None, call_name: str=None, hidden: bool=False):
    # split off the last dot as the function name, the rest is the module
    module, function = function_name.rsplit('.', maxsplit=1)
    # strip off any whitespace
    function = funtion.rstrip()
    # import the module
    module = importlib.import_module(module, package=None)
    # get the function from the module
    function = getattr(module, function)
    self.extend(function, alias=alias, name=call_name, hidden=hidden)

    values = {'function_name': function_name, 'alias': alias, 'call_name': call_name, 'hidden': hidden}

    self._config['extensions']['function_name'] = values
