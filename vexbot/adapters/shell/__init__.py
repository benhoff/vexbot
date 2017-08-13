# TODO: check to see if we can run concurrent using the prompt toolkit lib
# We've got two event loops: the communication poller and the response loop
import logging
import pprint
from threading import Thread as _Thread

from prompt_toolkit import AbortAction, CommandLineInterface
from prompt_toolkit.shortcuts import create_prompt_application, create_eventloop, create_output
from prompt_toolkit.token import Token
from prompt_toolkit.history import FileHistory
from prompt_toolkit.contrib.completers import WordCompleter
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.key_binding.bindings.completion import display_completions_like_readline

from vexbot import __version__


VEXBOT_SETTINGS_NAME = 'vexbot_shell'


class PromptShell:
    _NO_BOT = '<no bot detected>'
    def __init__(self,
                 command_manager,
                 history_filepath=None):

        self._bot = self._NO_BOT
        self.command_manager = command_manager
        self.messaging = self.command_manager.messaging
        self._thread = _Thread(target=self.run)
        self._thread.daemon = True
        self.running = False

        history = None
        if history_filepath is not None:
            history = FileHistory(history_filepath)

        self._history = history
        # NOTE: there's a sentence option here that might be interesting to explore
        self._completer = WordCompleter([], ignore_case=True)
        self._suggest = AutoSuggestFromHistory()

        def _get_prompt_tokens(*args):
            return [(Token.Prompt, self.prompt)]

        def _get_rprompt_tokens(*args):
            return [(Token.RPrompt, self._bot)]

        self.app = create_prompt_application(history=self._history,
                                             auto_suggest=AutoSuggestFromHistory(),
                                             get_prompt_tokens=_get_prompt_tokens,
                                             get_rprompt_tokens=_get_rprompt_tokens,
                                             enable_history_search=True,
                                             on_abort=AbortAction.RETRY)

        self.eventloop = create_eventloop()
        self.cli = CommandLineInterface(application=self.app,
                                        eventloop=self.eventloop,
                                        output=create_output(true_color=False))

        self._patch_context = self.cli.patch_stdout_context()

    @property
    def prompt(self):
        # profile = self.command_manager._profile
        profile = 'default'
        name = self.command_manager._robot_name
        return '{}[{}]: '.format(name, profile)

    def cmdloop_and_start_messaging(self):
        self._thread.start()
        self.cmdloop()

    def cmdloop(self, intro=None):
        if intro is None:
            intro = "Vexbot {}\n\n    Type \"help\" for command line help or \"commands\" for bot commands\n    NOTE: \"commands\" will only work if bot is running\n\n".format(__version__)
        print(intro, flush=True)
        while True:
            try:
                # FIXME
                if self._bot == self._NO_BOT:
                    self.command_manager.check_for_bot()
                    pass

                with self._patch_context:
                    result = self.cli.run(True)
                    self.command_manager.handle_command(result.text)
            except EOFError:
                break
        self.eventloop.close()

    def run(self):
        timeout = 3500
        while True
            for msg in self.messaging.run(timeout):
                if msg.type == 'RSP':
                    self._handle_response(msg)
            else:
                continue

            self.command_manager.check_for_bot()


    def _handle_response(self, message):
        header = message.contents.get('original', 'Response')
        contents = message.contents.get('response', None)
        pprint.pprint(contents, compact=True)

    def set_bot_prompt_no(self):
        if not self._bot == self._NO_BOT:
            self._bot = self._NO_BOT
            self.cli.request_redraw()

    def set_bot_prompt_yes(self, *args, **kwargs):
        if not self.prompt == '':
            self._bot = ''
            self.cli.request_redraw()

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
