import inspect as _inspect

from rx import Observer
from vexmessage import Request


class IrcObserver(Observer):
    def __init__(self, bot, messaging):
        super().__init__()
        self.bot = bot
        self.messaging = messaging
        self._commands = self._get_commands()

    def _get_commands(self) -> dict:
        result = {}
        for name, method in _inspect.getmembers(self):
            if name.startswith('do_'):
                result[name[3:]] = method

        return result

    def do_MSG(self, message, channel, *args, **kwargs):
        self.bot.privmsg(channel, message)

    def on_next(self, item: Request):
        command = item.command
        args = item.args
        kwargs = item.kwargs
        try:
            callback = self._commands[command]
        except KeyError:
            return

        try:
            result = callback(*args, **kwargs)
        except Exception as e:
            self.on_error(e, commnad)

        if result is None:
            return

        source = item.source
        self.messaging.send_control_response(source, result, command)

    def on_completed(self, *args, **kwargs):
        pass

    def on_error(self, *args, **kwargs):
        pass
