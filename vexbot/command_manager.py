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


def _msg_list_wrapper(func):
    """
    wraps methods that don't take the `msg` type.
    """
    def inner(msg):
        _, arg = _get_command_and_args(msg)
        commands = arg.split()

        return func(commands)

    inner.__doc__ = func.__doc__
    return inner


def _get_command_and_args(message):
    command = message.contents[0].strip()
    i, n = 0, len(command)
    while i < n and command[i] in INDENTCHARS: i = i + 1
    command, arg = command[:i], command[i:].strip()
    return command, arg


def _get_callback_recursively(callback: dict, commands):
    for command_number, command in enumerate(commands):
        result = callback.get(command, None)
        if result is None:
            break
        elif isinstance(result, dict):
            callback = result
        else:
            break

    return result, commands[:command_number]


class CommandManager:
    def __init__(self, robot):
        self._commands = {}
        self.indentchars = INDENTCHARS
        subprocess = {}

        s_manager = robot.subprocess_manager
        reg = robot.subprocess_manager.registered_subprocesses
        subprocess['settings'] = _msg_list_wrapper(s_manager.settings)

        self._commands['subprocess'] = subprocess

        self._commands['killall'] = _no_arg_wrapper(s_manager.killall)
        self._commands['restart_bot'] = _no_arg_wrapper(restart_bot)
        self._commands['commands'] = self._cmd_commands
        self._commands['alive'] = self._alive
        self._commands['help'] = _msg_list_wrapper(self._help)

        self._commands['start'] = _msg_list_wrapper(s_manager.start)
        self._commands['subprocesses'] = _no_arg_wrapper(reg)
        self._commands['restart'] = _msg_list_wrapper(s_manager.restart)
        self._commands['kill'] = _msg_list_wrapper(s_manager.kill)
        self._commands['running'] = _no_arg_wrapper(s_manager.running_subprocesses)
        self._messaging = robot.messaging

    def _cmd_commands(self, msg):
        """
        returns a list of all available commands
        """
        def get_stuff(d: dict):
            commands = []
            if not isinstance(d, dict):
                return commands

            for k, v in d.items():
                if isinstance(v, dict):
                    stuff = get_stuff(v)
                    for s in stuff:
                        commands.append(k + ' ' + s)
                else:
                    commands.append(k)
            return commands

        return get_stuff(self._commands)

    def parse_commands(self, msg):
        command, arg = _get_command_and_args(msg)
        commands = arg.split()
        if not command:
            return

        callback = self._commands.get(command, None)
        if callback:
            # Allow nesting of callbacks
            # reassign callback to the actual message
            if isinstance(callback, dict):
                callback, commands = _get_callback_recursively(callback,
                                                               commands)

                # callback can be None, handle that case and return from func
                # FIXME
                if callback is None:
                    self._messaging.send_response('Command not found',
                                                  target=msg.source,
                                                  original=command)

                    return

            results = callback(msg)
            if results:
                self._messaging.send_response(*results,
                                              target=msg.source,
                                              original=command)

            return

        if not callback:
            self._messaging.send_response('Command not found',
                                          target=msg.source,
                                          original=command)

    def _help(self, args):
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

    def _alive(self, msg):
        """
        queries the subprocesses to check their status using messaging.

        can also use the `running` command to see what's running locally
        """
        # FIXME
        values = list(self._commands['subprocess']['subprocesses']())
        if values:
            try:
                values.remove(msg.source)
            except ValueError:
                pass
            for v in values:
                self._messaging.send_command('alive', target=v)
