import sys as _sys
import logging # flake8: noqa
import collections as _collections
import inspect as _inspect

from rx import Observer

from vexmessage import Request


class BotObserver(Observer):
    def __init__(self,
                 messaging,
                 subprocess_manager: 'vexbot.subprocess_manager.SubprocessManager'):

        super().__init__()
        self.messaging = messaging
        self.subprocess_manager = subprocess_manager
        self._commands = self._get_commands()

    def _get_commands(self) -> dict:
        result = {}
        for name, method in _inspect.getmembers(self):
            if name.startswith('do_'):
                result[name[3:]] = method

        return result

    def do_start(self, name: str, mode: str='replace'):
        self.subprocess_manager.start(name, mode)

    def do_bot_commands(self, *args, **kwargs):
        commands = tuple(self._commands.keys())
        return commands

    def do_restart(self, name: str, mode: str='replace'):
        self.subprocess_manager.restart(name, mode)

    def do_stop(self, name: str, mode: str='replace'):
        self.subprocess_manager.stop(name, mode)

    def on_next(self, item: Request):
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

    def on_error(self, *args, **kwargs):
        pass

    def on_completed(self, *args, **kwargs):
        pass

    def do_kill_bot(self, *args, **kwargs):
        """
        Kills the instance of vexbot
        """
        _sys.exit()
