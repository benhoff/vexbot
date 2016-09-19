import sys as _sys
import cmd as _cmd
import textwrap as _textwrap

from vexbot.adapters.messaging import ZmqMessaging as _Messaging
from vexbot.command_managers import CommandManager as _Command
from vexbot.settings_manager import SettingsManager as _SettingsManager

from vexbot.commands.start_vexbot import start_vexbot as _start_vexbot


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

    def do_update_robot_settings(self, arg):
        if arg == '':
            self.do_contexts('')

        self.do_create_robot_settings(arg)

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

            self.messaging._pub_address = settings.publish_address
            self.messaging._sub_address = settings.subscribe_address
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

    def do_create_robot_settings(self, arg):
        s = ('Default values are shown in `[]` after the prompt name. Pressin'
             'g enter accepts the default value')

        self.stdout.write('\n' + _textwrap.fill(s,
                                                initial_indent='    ',
                                                subsequent_indent='        ')
                               + '\n\n')

        s = {}
        if arg == '':
            arg = 'default'

        s['context'] = self._prompt_helper('context [{}]: '.format(arg), arg)
        if s['context'] is None:
            self.stdout.write('\n')
            return

        s.update(self._get_old_settings(self.settings_manager,
                                        s['context']))

        s['name'] = self._prompt_helper('name [{}]: '.format(s.get('name', 'vexbot')),
                                        s.get('name', 'vexbot'))

        if s['name'] is None:
            self.stdout.write('\n')
            return

        s['subscribe_address'] = self._prompt_helper('subscribe_address [{}]: '.format(s.get('subscribe_address',
                                                                                       'tcp://127.0.0.1:4000')),
                                               s.get('subscribe_address',
                                                     'tcp://127.0.0.1:4000'))

        if s['subscribe_address'] is None:
            self.stdout.write('\n')
            return

        s['publish_address'] = self._prompt_helper('publish address [{}]: '.format(s.get('publish_address', 'tcp://127.0.0.1:4001')),
                                               s.get('publish_address', 'tcp://127.0.0.1:4001'))

        if s['publish_address'] is None:
            self.stdout.write('\n')
            return

        s['monitor_address'] = self._prompt_helper('monitor address [{}]: '.format(s.get('monitor_address', '')),
                                               s.get('monitor_address', ''))

        if s['monitor_address'] is None:
            self.stdout.write('\n')
            return

        # FIXME
        starting_adapters = ' '.join(s.get('startup_adapters', ()))

        starting_adapters = self._prompt_helper('starting adapters [{}]: '.format(starting_adapters),
                                                starting_adapters)

        if starting_adapters is not None:
            starting_adapters = starting_adapters.lower().split()
        else:
            starting_adapters = []

        s['startup_adapters'] = starting_adapters

        if 'id' in s:
            self.settings_manager.update_robot_model(s)
        else:
            self.settings_manager.create_robot_model(s)

        if s['context'] == self._context:
            self.do_context(self._context)

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
