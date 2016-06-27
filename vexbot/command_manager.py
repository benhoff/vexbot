import os
import sys
import string

from vexbot.commands.restart_bot import restart_bot


INDENTCHARS = string.ascii_letters + string.digits + '_'

def _no_arg_wrapper(func):
    """
    wraps methods that don't take args so that the method
    can be called without error
    """
    def inner(*args):
        return func()

    inner.__doc__ = func.__doc__
    return inner


class CommandManager:
    def __init__(self, robot):
        self._commands = {}
        self.indentchars = INDENTCHARS
        self._commands['start'] = robot.subprocess_manager.start
        self._commands['restart'] = robot.subprocess_manager.restart
        self._commands['kill'] = robot.subprocess_manager.kill

        run = robot.subprocess_manager.running_subprocesses
        self._commands['running'] = _no_arg_wrapper(run)

        reg = robot.subprocess_manager.registered_subprocesses
        self._commands['registered'] = _no_arg_wrapper(reg)
        killall = robot.subprocess_manager.killall
        # wrap killall command with dummy func to avoid error
        # with passing in args
        self._commands['killall'] = _no_arg_wrapper(killall)
        self._commands['settings'] = robot.subprocess_manager.settings
        self._commands['restart_bot'] = _no_arg_wrapper(restart_bot)
        self._commands['commands'] = self._cmd_commands
        self._commands['alive'] = self._alive
        self._commands['help'] = self._help

        self._messaging = robot.messaging

    def _cmd_commands(self, *args):
        return tuple(self._commands.keys())

    def parse_commands(self, msg):
        command = msg.contents[0].strip()
        if not command:
            return
        i, n = 0, len(command)
        while i < n and command[i] in self.indentchars: i = i + 1
        command, arg = command[:i], command[i:].strip()
        commands = arg.split()

        callback = self._commands.get(command, None)
        if callback:
            results = callback(commands)
            if results:
                self._messaging.send_response(*results,
                                              target=msg.source,
                                              original=command)

            return

    def _help(self, *args):
        if not args:
            return self._commands()
        else:
            docs = []
            for arg in args:
                doc = self._commands.get(arg, None).__doc__
                if doc:
                    docs.append(doc)

            if docs:
                return docs

    def _alive(self, *args):
        values = self._commands['registered']()
        if values:
            try:
                values.remove(msg.source)
            except ValueError:
                pass
            for v in values:
                self._messaging.send_command('alive', target=v)
