import sys
import logging # flake8: noqa
import collections as _collections
from threading import RLock as _RLock

from vexmessage import Request

from vexbot.commands.restart_bot import restart_bot as _restart_bot
from vexbot.util.function_wrapers import (msg_list_wrapper,
                                          no_arguments)

class Observable:
    def __init__(self):
        self.observers = []
        self.mutex = _RLock()
        self.changed = False

    def add_observer(self, observer):
        if observer not in self.obs:
            self.obs.append(observer)

    def delete_observer(self, observer):
        self.obs.remove(observer)

    def notify_observers(self, message):
        for observer in self.observers:
            observer.update(self, message)

    def delete_observers(self):
        self.observers = []

    def set_changed(self):
        self.changed = True

    def clear_changed(self):
        self.changed = False

    def has_changed(self):
        return self.changed

    def count_observers(self):
        return len(self.observers)


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
        gcr = self._get_callback_recursively
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


class BotCommandManager(CommandManager):
    def __init__(self, robot: 'vebot.robot:Robot'):
        # Need to pass in messaging in order to access commands
        # Alternatively, could pass in some sort of interface
        super().__init__(robot.messaging)
        # nested command dict
        subprocess = {}

        adapter_interface = robot.adapter_interface

        # alias for pep8
        # FIXME: Should probably access this a better way
        s_manager = adapter_interface.get_subprocess_manager()

        # FIXME: use the settings manager instead of subprocess manager
        # subprocess['settings'] = msg_list_wrapper(s_manager.get_settings, 1)

        # self._commands['subprocess'] = subprocess

        # self._commands['killall'] = no_arguments(adapter_interface.killall)
        # self._commands['restart_bot'] = no_arguments(_restart_bot)

        # TODO: check if want this to be `start_adapters` or `start_adapter`
        # self._commands['start'] = msg_list_wrapper(adapter_interface.start_adapters)
        # self._commands['stop'] = msg_list_wrapper(s_manager.stop)
        # registered = s_manager.registered_subprocesses
        # self._commands['subprocesses'] = no_arguments(registered)
        # self._commands['restart'] = msg_list_wrapper(s_manager.restart)
        # self._commands['kill'] = msg_list_wrapper(s_manager.kill)
        # self._commands['kill_bot'] = self._kill_bot
        running = s_manager.running_subprocesses
        # self._commands['running'] = no_arguments(running)

    def _kill_bot(self, *args, **kwargs):
        """
        Kills the instance of vexbot
        """
        sys.exit()


class AdapterCommandManager(CommandManager):
    def __init__(self, messaging: 'vexbot.messaging:Messaging'):
        super().__init__(messaging)
        self._commands['alive'] = no_arguments(self._alive)

    def _alive(self, *args):
        self._messaging.send_status('CONNECTED')
