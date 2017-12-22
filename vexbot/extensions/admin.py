import pip
import inspect


def install(self, *args, **kwargs):
    pip.main(['install', *args])


def uninstall(self, *args, **kwargs):
    pip.main(['uninstall', *args])


def update(self, *args, **kwargs):
    pip.main(['install', '--upgrade', *args])


def get_commands(self, *args, **kwargs):
    # TODO: add in a short summary
    # TODO: also end in some entity parsing? or getting of the args and
    # kwargs
    commands = self._commands.keys()
    return sorted(commands, key=str.lower)


def get_disabled(self, *args, **kwargs):
    commands = self._config['disabled'].keys()
    return sorted(commands, key=str.lower)


def disable(self, name: str, *args, **kwargs):
    self._commands.pop(name)


def get_command_modules(self, *args, **kwargs):
    result = set()
    for cb in self._commands.values():
        module = inspect.getmodule(cb)
        result.add(module.__name__)
    # TODO: Test to see if this works like I think it will
    if args:
        result = set(args).intersection(result)
    return result


def get_cache(self, *args, **kwargs):
    return dict(self._config)


def delete_cache(self, *args, **kwargs):
    pass
