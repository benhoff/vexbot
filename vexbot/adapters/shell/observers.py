import sys as _sys
import cmd as _cmd
import textwrap as _textwrap
import shlex as _shlex
import pprint as _pprint
import logging

from gi._error import GError
from pydbus import SessionBus, SystemBus
from rx import Observer

from prompt_toolkit.shortcuts import print_tokens
from pygments.styles.monokai import MonokaiStyle
from prompt_toolkit.styles import style_from_pygments
from pygments.token import Token

from vexmessage import Message

from vexbot.subprocess_manager import SubprocessManager

from vexbot.adapters.shell.parser import parse


class PrintObserver(Observer):
    style = style_from_pygments(MonokaiStyle)

    def on_next(self, msg: Message):
        tokens = [(Token.Keyword, '{}: '.format(msg.contents['author'])),
                  (Token, msg.contents['message']),
                  (Token, '\n')]

        print_tokens(tokens, style=self.style)

    def on_error(self, *args, **kwargs):
        pass

    def on_completed(self, *args, **kwargs):
        pass


class CommandObserver(Observer):
    def __init__(self,
                 messaging,
                 stdin=None,
                 stdout=None):

        self.shebangs = ['!',]
        self.subprocess_manager = SubprocessManager()

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

    def on_error(self, error: Exception, text: str, *args, **kwargs):
        if isinstance(error, GError):
            print(error.message)
            command = self._get_command(text)
            if command in ('start', 'restart', 'status'):
                print('You might need to add `.target` to the end of the command')
            return
        print(error.message)

    def on_completed(self, *args, **kwargs):
        pass

    def on_next(self, *args, **kwargs):
        pass

    def set_on_bot_callback(self, callback):
        self._bot_callback = callback

    def set_no_bot_callback(self, callback):
        self._no_bot_callback = callback

    def do_ping(self, *args, **kwargs):
        self.messaging.send_ping()

    def _get_command(self, arg: str):
        # consume shebang
        arg = arg[1:]
        # Not sure if `shlex` can handle unicode. If can, this can be done
        # here rather than having a helper method
        args = _shlex.split(arg)
        try:
            return args.pop(0)
        except IndexError:
            return

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
            # TODO: Notify user of fallthrough?
            self.messaging.send_command(command, args=args, kwargs=kwargs) 
            return

        result = callback(*args, **kwargs)
        return result

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

    def do_status(self, program: str, *args, **kwargs):
        status = self.subprocess_manager.status(program)
        return status


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
