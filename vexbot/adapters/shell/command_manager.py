import sys as _sys
import cmd as _cmd
import textwrap as _textwrap

from vexbot.adapters.messaging import ZmqMessaging as _Messaging
from vexbot.command_managers import CommandManager as _Command
from vexbot.settings_manager import SettingsManager as _SettingsManager

from vexbot.commands.start_vexbot import start_vexbot as _start_vexbot
from vexbot.adapters.shell.tui import VexTextInterface


class ShellCommand(_Command):
    identchars = _cmd.IDENTCHARS
    def __init__(self,
                 context='default',
                 messaging=None,
                 stdin=None,
                 stdout=None):

        super().__init__(messaging)
        self.remove_command('commands')
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
        self.settings_manager = _SettingsManager(context=context)
        self._text_interface = VexTextInterface(self.settings_manager)

        self._context = context
        self.do_context(context)
        for method in dir(self):
            if method.startswith('do_'):
                self._commands[method[3:]] = getattr(self, method)

    def handle_command(self, arg):
        if self.is_command(arg, call_command=True):
            # NOTE: since `call_command=True`, command will already be called
            pass
        else:
            command, argument, line = self._parseline(arg)
            print(command, argument)

            self.messaging.send_command(command=command,
                                        args=argument,
                                        line=line)

            if self._context is None:
                self.stdout.write('\nNo context set! Use `contexts` to see '
                                  'stored robot contexts and the `context` '
                                  'command to set the shell context\n\n')

    def _parseline(self, line):
        """Parse the line into a command name and a string containing
        the arguments.  Returns a tuple containing (command, args, line).
        'command' and 'args' may be None if the line couldn't be parsed.
        """
        line = line.strip()
        if not line:
            return None, None, line
        elif line[0] == '?':
            line = 'help ' + line[1:]
        elif line[0] == '!':
            if hasattr(self, 'do_shell'):
                line = 'shell ' + line[1:]
            else:
                return None, None, line
        i, n = 0, len(line)
        while i < n and line[i] in self.identchars: i = i+1
        cmd, arg = line[:i], line[i:].strip()
        return cmd, arg, line

    def do_start_bot(self, arg):
        if arg == '':
            arg = self._context
        _start_vexbot(arg)

    def do_context(self, arg):
        if arg:
            return self.do_contexts(arg)
        context = self._context
        if context is None:
            context = 'NONE SET'
        self.stdout.write('\n' + context + '\n\n')

    def do_contexts(self, arg):
        if arg:
            # Do this first for now, in case our user messes up
            settings = self.settings_manager.get_robot_model(arg)
            if settings is None:
                return
            m = self.messaging
            # FIXME----
            if m._pub_address:
                m.pub_socket.disconnect(m._pub_address)
            if m._sub_address:
                m.sub_socket.disconnect(m._sub_address)
            # ------

            self.messaging._pub_address = settings.zmq_publish_address
            self.messaging._sub_address = settings.zmq_subscription_addresses
            self.messaging.update_messaging()
            self._context = arg
        else:
            contexts = self.settings_manager.get_robot_contexts()
            self.stdout.write('\n')
            self.print_topics('contexts',
                              contexts,
                              15,
                              80)

    def _get_old_settings(self, setting_manager, context):
        """
        returns settings minus the `_sa_instance_state`
        used in `do_create_robot_settings` and changes the
        adapters to just be their names.
        """
        old_settings = self.settings_manager.get_robot_model(context)
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
