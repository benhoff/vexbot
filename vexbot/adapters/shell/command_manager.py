import sys as _sys
import cmd as _cmd
import textwrap as _textwrap
import shlex as _shlex
import pprint as _pprint
import logging

from gi._error import GError
from pydbus import SessionBus, SystemBus

from vexbot.adapters.messaging import ZmqMessaging as _Messaging
from vexbot.command_managers import CommandManager as _Command
from vexbot.subprocess_manager import SubprocessManager

from vexbot.adapters.tui import VexTextInterface

from vexbot.adapters.shell.parser import parse


class ShellCommand:
    def __init__(self,
                 messaging=None,
                 stdin=None,
                 stdout=None):

        self.shebangs = ['!',]
        self.subprocess_manager = SubprocessManager()

        if stdin is None:
            stdin = _sys.stdin
        if stdout is None:
            stdout = _sys.stdout

        self.stdin = stdin
        self.stdout = stdout

        if messaging is None:
            messaging = _Messaging('shell', socket_filter='shell')

        self.messaging = messaging
        self.messaging.start_messaging()

        self._bot_callback = None
        self._no_bot_callback = None
        self._commands = {}
        for method in dir(self):
            if method.startswith('do_'):
                self._commands[method[3:]] = getattr(self, method)

    def is_command(self, text: str):
        """
        checks for presence of shebang in the first character of the text
        """
        if text[0] in self.shebangs:
            return True

        return False

    def set_on_bot_callback(self, callback):
        self._bot_callback = callback

    def set_no_bot_callback(self, callback):
        self._no_bot_callback = callback

    def check_for_bot(self):
        self.messaging.send_ping()

    def do_ping(self, *args, **kwargs):
        self.messaging.send_ping()

    def handle_command(self, arg: str):
        # consume shebang
        arg = arg[1:]
        # Not sure if `shlex` can handle unicode. If can, this can be done
        # here rather than having a helper method
        args = _shlex.split(arg)
        try:
            command = args.pop(0)
        except IndexError:
            return

        args, kwargs = parse(args)
        try:
            callback = self._commands[command]
        except KeyError:
            # TODO: error handling or fallthrough
            return
        result = callback(*args, **kwargs)

        """
        self.messaging.send_command(command=command,
                                    args=args,
                                    kwargs=kwargs)
        """

    def do_start(self, program: str, *args, **kwargs):
        mode = kwargs.get('mode', 'replace')
        # TODO: Better aliasing for more commands
        if program == 'bot':
            program = 'vexbot'
        if (not program.endswith('.service') or
                not program.endswith('.target') or
                not program.endswith('.socket')):
            program = program + '.service'

        self.subprocess_manager.start(program, mode)


    def do_restart(self, program: str, *args, **kwargs):
        mode = kwargs.get('mode', 'replace')
        if program == 'bot':
            program = 'vexbot'

        if (not program.endswith('.service') or
                not program.endswith('.target') or
                not program.endswith('.socket')):
            program = program + '.service'

        self.subprocess_manager.restart(program, mode)


    def do_stop(self, program: str, *args, **kwargs):
        mode = kwargs.get('mode', 'replace')
        if program == 'bot':
            program = 'vexbot'

        if (not program.endswith('.service') or
                not program.endswith('.target') or
                not program.endswith('.socket')):
            program = program + '.service'

        self.subprocess_manager.stop(program, mode)


    def do_commands(self, *args, **kwargs):
        commands = ['!' + x for x in self._commands.keys()]
        _pprint.pprint(commands)
