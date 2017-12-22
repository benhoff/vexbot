import pip


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
