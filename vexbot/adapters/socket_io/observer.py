import inspect as _inspect

from rx import Observer
from vexmessage import Request


class SocketObserver(Observer):
    def __init__(self, bot, messaging):
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

    def do_commands(self, *args, **kwargs):
        return list(self._commands.keys())

    def on_error(self, *args, **kwargs):
        pass

    def on_completed(self, *args, **kwargs):
        pass

    def do_help(self, *arg, **kwargs):
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
