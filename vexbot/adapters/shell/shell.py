import cmd as _cmd
import atexit as _atexit

from vexbot import __version__


class Shell(_cmd.Cmd):
    def __init__(self,
                 command_manager,
                 prompt_name='vexbot',
                 already_running=False,
                 history_filepath=None):

        super().__init__()
        self.command_manager = command_manager
        self._set_readline_helper(history_filepath)
        self.prompt = prompt_name + ': '
        self.running = False
        # FIXME
        self.misc_header = "Commands"

        self.stdout.write('Vexbot {}\n'.format(__version__))
        if already_running:
            self.stdout.write('vexbot already running\n')
        self.stdout.write("    Type \"help\" for command line help or "
                          "\"commands\" for bot commands\n    NOTE: "
                          "\"commands\" will only work if bot is running\n\n")

    def cmdloop(self, intro=None):
        self.running = True
        super().cmdloop(intro)

    def default(self, arg):
        self.command_manager.handle_command(arg)

    def _set_readline_helper(self, history_file=None):
        try:
            import readline
        except ImportError:
            return

        try:
            readline.read_history_file(history_file)
        except IOError:
            pass
        readline.set_history_length(1000)
        _atexit.register(readline.write_history_file, history_file)

    def _create_command_function(self, command):
        """
        used to help add completions
        """
        def resulting_function(arg):
            self.default(' '.join((command, arg)))

        return resulting_function

    def get_names(self):
        names = dir(self)
        # NOTE: Adds the names from the command manager to the autocomplete
        # helper
        names.extend(['do_' + a for
                      a in
                      self.command_manager._commands.keys()])
        return names

    def do_help(self, arg):
        if arg:
            if self.command_manager.is_command(arg):
                doc = self.command_manager._commands[arg].__doc__
                if doc:
                    self.stdout.write("{}\n".format(str(doc)))
            else:
                self.command_manager.messaging.send_command(command='help',
                                                            args=arg)

        else:
            self.stdout.write("{}\n".format(self.doc_leader))
            # TODO: add commands from shell
            commands = set(self.command_manager._commands.keys())
            commands.update(x[3:] for
                            x in
                            self.get_names() if
                            x.startswith('do_'))

            commands.add('commands')
            commands = '\n'.join(commands)

            self.print_topics(self.misc_header,
                              [commands],
                              15,
                              80)

    def add_completion(self, command):
        setattr(self,
                'do_{}'.format(command),
                self._create_command_function(command))

    def do_EOF(self, arg):
        self.stdout.write('\n')
        self.running = False
        return True


def main(**kwargs):
    if not kwargs:
        kwargs = {}
    shell = Shell(**kwargs)
    shell.cmdloop()


if __name__ == '__main__':
    main()
