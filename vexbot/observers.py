import sys as _sys
import logging # flake8: noqa
import collections as _collections
import inspect as _inspect

from rx import Observer

from vexmessage import Request
from vexbot.messaging import Messaging


class BotObserver(Observer):
    def __init__(self,
                 messaging: Messaging,
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

    # FIXME: this API is brutal
    def do_CMD(self, *args, **kwargs):
        try:
            target = kwargs.pop('target')
            command = kwargs.pop('remote_command')
        except KeyError:
            return
        try:
            kwargs.pop('source')
        except KeyError:
            pass

        source = self.messaging._address_map[target]
        # FIXME: Figure out a better API for this
        self.messaging.send_control_response(source, command, *args, **kwargs)

    def do_MSG(self, target, *args, **kwargs):
        try:
            kwargs.pop('source')
        except KeyError:
            pass
        source = self.messaging._address_map[target]
        # FIXME: Figure out a better API for this
        self.messaging.send_control_response(source, 'MSG', *args, **kwargs)

    def do_IDENT(self, source, *args, **kwargs):
        service_name = kwargs.get('service_name')
        if service_name is None:
            return

        self.messaging._address_map[service_name] = source

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
        source = item.source
        try:
            callback = self._commands[command]
        except KeyError:
            return

        try:
            result = callback(*args, **kwargs, source=source)
        except Exception as e:
            self.on_error(e, command)
            return

        if result is None:
            return

        source = item.source
        # FIXME: figure out a better API for this
        self.messaging.send_control_response(source, command, result=result)

    # FIXME: do better logging
    def on_error(self, *args, **kwargs):
        print(args)

    def on_completed(self, *args, **kwargs):
        pass

    def do_kill_bot(self, *args, **kwargs):
        """
        Kills the instance of vexbot
        """
        _sys.exit()
