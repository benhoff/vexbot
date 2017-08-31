import sys as _sys
import cmd as _cmd
import textwrap as _textwrap
import shlex as _shlex
import logging

from gi._error import GError
from pydbus import SessionBus, SystemBus

from vexbot.adapters.messaging import ZmqMessaging as _Messaging
from vexbot.command_managers import CommandManager as _Command
from vexbot.settings_manager import SettingsManager as _SettingsManager

from vexbot.commands.start_vexbot import start_vexbot as _start_vexbot
from vexbot.adapters.tui import VexTextInterface

from vexbot.adapters.shell.parser import parse


class ShellCommand:
    def __init__(self,
                 messaging=None,
                 stdin=None,
                 stdout=None):

        self.using_session_bus = True
        self.shebangs = ['!',]
        try:
            self.bus = SessionBus()
        except GError:
            self.using_session_bus = False
        self.system_bus = SystemBus()

        if self.using_session_bus:
            self.systemd = self.bus.get('.systemd1')
        else:
            self.systemd = self.system_bus.get('.systemd1')

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
        self.settings_manager = _SettingsManager()
        self._text_interface = VexTextInterface(self.settings_manager)
        self._robot_name = 'vexbot'

        self._bot_callback = None
        self._no_bot_callback = None
        """
        for method in dir(self):
            if method.startswith('do_'):
                self._commands[method[3:]] = getattr(self, method)
        """

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

    def send_command_to_bot(self, arg):
        pass

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
        print(args, kwargs)
        self.messaging.send_command(command=command,
                                    args=args,
                                    kwargs=kwargs)

    def do_start_bot(self, arg):
        if arg == '':
            arg = self._profile
        _start_vexbot(arg)


    def _get_old_settings(self, setting_manager, profile):
        """
        returns settings minus the `_sa_instance_state`
        used in `do_create_robot_settings` and changes the
        adapters to just be their names.
        """
        old_settings = self.settings_manager.get_robot_model(profile)
        if old_settings is None:
            return dict()
        adapters = [x.name for x in old_settings.startup_adapters]
        old_settings = dict(old_settings.__dict__)
        old_settings.pop('_sa_instance_state')
        old_settings['startup_adapters'] = adapters
        return old_settings

    def do_robot_settings(self, arg):
        self._text_interface.robot_settings()

        # TODO: implement
        """
        if 'id' in s:
            self.settings_manager.update_robot_model(s)
        else:
            self.settings_manager.create_robot_model(s)

        if s['context'] == self._context:
            self.do_context(self._context)
        """

    def do_irc_settings(self, arg):
        irc_settings()

    def do_xmpp_settings(self, arg):
        xmpp_settings()

    def do_youtube_settings(self, arg):
        youtube_settings()

    def do_socket_io_settings(self, arg):
        socket_io_settings()

    def _prompt_helper(self, prompt, default=None):
        """
        used in `do_create_robot_settings`
        creates a prompt for the user and suggests a default value
        """
        self.stdout.write(prompt)
        self.stdout.flush()
        line = self.stdin.readline()
        if not len(line):
            line = 'EOF'
        else:
            line = line.rstrip('\r\n')

        if line not in ('EOF', 'STOP'):
            if line == '' and default is not None:
                line = default

            # TODO: Clean up
            self.stdout.write('    ' + line + '\n\n')

            return line

        return None
