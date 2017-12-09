import inspect as _inspect
from vexbot.extension import extension
from vexbot.observers import CommandObserver


@extension(CommandObserver)
def do_code(self, *args, **kwargs):
    """
    get the python source code from callback
    """
    callback = self._commands[args[0]]
    # TODO: syntax color would be nice
    source = _inspect.getsourcelines(callback)[0]
    """
    source_len = len(source)
    source = PygmentsLexer(CythonLexer).lex_document(source)()
    """
    # FIXME: formatting sucks
    return "\n" + "".join(source)
