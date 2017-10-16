import inspect as _inspect

from rx import Observer
from vexmessage import Request


class IrcObserver(Observer):
    def __init__(self, messaging):
        super().__init__()
        self.messaging = messaging
        self._commands = self._get_commands()

    def _get_commands(self) -> dict:
        result = {}
        for name, method in _inspect.getmembers(self):
            if name.startswith('do_'):
                result[name[3:]] = method

        return result

    def do_MSG(self, *args, **kwargs):
        print(args, kwargs)

    def on_next(self, item: Request):
        command = item.command
        args = item.args
        kwargs = item.kwargs
        print(command, args, kwargs)
        try:
            callback = self._commands[command]
        except KeyError:
            return

        result = callback(*args, **kwargs)

        if result is None:
            return

        source = item.source
        self.messaging.send_control_response(source, result, command)

    def on_completed(self, *args, **kwargs):
        pass

    def on_error(self, *args, **kwargs):
        pass
