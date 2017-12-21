import pkg_resources


def get_all_extensions(self, *args, **kwargs):
    name = 'vexbot_extensions'
    verify_requirements = True
    extensions = [x.name for x in pkg_resources.iter_entry_points(name)]
    """
    if (hasattr(entry_point, 'resolve') and hasattr(entry_point, 'require')):
        if verify_requirements:
            entry_point.require()
            plugin = entry_point.resolve()
        else:
            plugin = entry_point.load()

        result.append(entry_point.name)
    """
    return extensions


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


