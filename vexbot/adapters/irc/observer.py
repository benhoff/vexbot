from rx import Observer


class IrcObserver(Observer):
    def __init__(self, messaging, subprocess_manager: SubprocessManager=None):
        super().__init__()
        self.messaging = messaging
        self.subprocess_manager = subprocess_manager or SubprocessManager()
        self._commands = self._get_commands()

    def _get_commands(self) -> dict:
        result = {}
        for name, method in _inspect.getmembers(self):
            if name.startswith('do_'):
                result[name[3:]] = method

        return result

    def on_next(self, *args, **kwargs):
        command = item.command
        args = item.args
        kwargs = item.kwargs
        try:
            callback = self._commands[command]
        except KeyError:
            return

        result = callback(*args, **kwargs)

        if result is None:
            return

        source = item.source
        self.messaging.send_control_response(source, result, command)

    def on_complete(self, *args, **kwargs):
        pass

    def on_error(self, *args, **kwargs):
        pass
