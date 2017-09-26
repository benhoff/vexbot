import sys as _sys
import logging # flake8: noqa
import collections as _collections
import inspect as _inspect

from rx import Observer

from vexmessage import Request

from vexbot.subprocess_manager import SubprocessManager
from vexbot.util.function_wrapers import (msg_list_wrapper,
                                          no_arguments)

class CommandManager:
    def __init__(self, messaging: 'vexbot.messaging:Messaging'):
        # NOTE: commands is a dict of dicts and there is nested parsing
        self.observers = {}
        self._messaging = messaging
        # self._commands['commands'] = self._cmd_commands

    def register_command(self,
                         command: str,
                         function_or_dict: (_collections.Callable, dict)):
        """
        `func_or_nested` can either be a function or a dictionary
        """
        self._commands[command] = function_or_dict

    def parse_commands(self, msg: Request):
        command = msg.contents.get('command')

        if not command:
            return

        args = msg.contents.get('args')

        callback, command, args = self._get_callback_recursively(command, args)
        msg.contents['parsed_args'] = args

        if callback:
            results = callback(msg)

            if results:
                self._messaging.send_response(target=msg.source,
                                              original=command,
                                              response=results)

    def process_command(self, message: Request):
        raise RuntimeError('Not Implemented')
        # Do we want to do an observable system or callback system?
        callback, command, args = gcr(message.command, message.args)

        if callback:
            results = callback(message)

        return results

    def _cmd_commands(self, msg: Request):
        """
        returns a list of all available commands
        works recursively
        """
        def get_commands(d: dict):
            """
            recursive command
            """
            commands = []
            if not isinstance(d, dict):
                return commands

            for k, v in d.items():
                if isinstance(v, dict):
                    # NOTE: recursive command
                    stuff = get_commands(v)
                    for s in stuff:
                        commands.append(k + ' ' + s)
                else:
                    commands.append(k)
            return commands

        return get_commands(self._commands)


class BotCommands(Observer):
    def __init__(self, messaging, subprocess_manager: SubprocessManager):
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
