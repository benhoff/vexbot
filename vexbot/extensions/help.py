def help(self, *arg, **kwargs):
    """
    Help helps you figure out what commands do.
    Example usage: !help code
    To see all commands: !commands
    """
    name = arg[0]
    try:
        callback = self._commands[name]
    except KeyError:
        self._logger.info(' !help not found for: %s', name)
        return self.do_help.__doc__

    return callback.__doc__
