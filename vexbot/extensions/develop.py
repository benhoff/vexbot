import inspect as _inspect


def get_code(self, *args, **kwargs):
    """
    get the python source code from callback
    """
    # FIXME: Honestly should allow multiple commands
    callback = self._commands[args[0]]
    # TODO: syntax color would be nice
    source = _inspect.getsourcelines(callback)[0]
    """
    source_len = len(source)
    source = PygmentsLexer(CythonLexer).lex_document(source)()
    """
    # FIXME: formatting sucks
    return "\n" + "".join(source)


def get_members(self, *args, **kwargs):
    return [x[0] for x in _inspect.getmembers(self)]


def get_commands(self, *args, **kwargs):
    # TODO: add in a short summary
    # TODO: also end in some entity parsing? or getting of the args and
    # kwargs
    commands = self._commands.keys()
    return sorted(commands, key=str.lower)
