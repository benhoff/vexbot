from vexbot.extension import extension
from vexbot.observers import CommandObserver


@extension(CommandObserver)
def do_hidden(self, *args, **kwargs):
    results = []
    for k, v in self._commands.items():
        if hasattr(v, 'hidden') and v.hidden:
            results.append('!' + k)
        else:
            continue
    return results
