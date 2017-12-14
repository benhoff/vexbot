import inspect as _inspect

from vexmessage import Request
from vexbot.observer import Observer
from vexbot.extensions import develop
from vexbot.extensions import help as vexhelp


class SocketObserver(Observer):
    extensions = (develop.get_code, develop.get_commands, vexhelp.help)
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

    def do_MSG(self, message, *args, **kwargs):
        msg_target = kwargs.get('msg_target')
        if msg_target:
            message = msg_target + ', ' + message

        data = {}
        data['name'] = 'message'
        data['args'] = [message, self.bot._streamer_name]

        # FIXME: this API is awful.
        self.bot.send_packet_helper(5, data)

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
            self.on_error(e, command, args)
            return

        if result is None:
            return

        source = item.source
        self.messaging.send_command_response(source, command, result=result, *args, **kwargs)

    def on_error(self, *args, **kwargs):
        pass

    def on_completed(self, *args, **kwargs):
        pass
