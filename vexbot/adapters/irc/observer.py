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
        msg_target = kwargs.get('msg_target')
        if msg_target:
            message = msg_target + ', ' + message
        self.bot.privmsg(channel, message)

    def do_join(self, *args, **kwargs):
        self.bot.join(*args)

    def do_part(self, *args, **kwargs):
        self.bot.part(*args)

    def do_kick(self, channel, target, reason=None, *args, **kwargs):
        self.bot.kick(channel, target, reason)

    def do_away(self, message=None, *args, **kwargs):
        self.bot.away(message)

    def do_unaway(self, *args, **kwargs):
        self.bot.unaway()

    def do_topic(self, channel, topic=None, *args, **kwargs):
        self.bot.topic(channel, topic)

    def do_commands(self, *args, **kwargs):
        return self._get_commands()

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
        self.messaging.send_control_response(source, result, command)

    def on_completed(self, *args, **kwargs):
        pass

    def on_error(self, *args, **kwargs):
        print(args)
