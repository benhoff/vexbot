import pip


def install(self, *args, **kwargs):
    pip.main(['install', *args])


def uninstall(self, *args, **kwargs):
    pip.main(['uninstall', *args])


def update(self, *args, **kwargs):
    pip.main(['install', '--upgrade', *args])


def enable(self, *args, **kwargs):
    for arg in args:
        try:
            callback = self._disabled.pop(arg)
        except KeyError:
            continue
        self._commands[arg] = callback


def disable(self, *args, **kwargs):
    for arg in args:
        try:
            callback = self._commands.pop(arg)
        except KeyError:
            continue
        self._disabled[arg] = callback


def get_commands(self, *args, **kwargs):
    # TODO: add in a short summary
    # TODO: also end in some entity parsing? or getting of the args and
    # kwargs
    commands = self._commands.keys()
    return sorted(commands, key=str.lower)


def get_disabled(self, *args, **kwargs):
    commands = self._disabled.keys()
    return sorted(commands, key=str.lower)
