# TODO: check to see if we can run concurrent using the prompt toolkit lib
# We've got two event loops: the communication poller and the response loop
import logging as _logging
import pprint as _pprint
from threading import Thread as _Thread

from prompt_toolkit import AbortAction, CommandLineInterface
from prompt_toolkit.shortcuts import create_prompt_application, create_eventloop, create_output
from prompt_toolkit.token import Token as _Token
from prompt_toolkit.history import FileHistory as _FileHistory
from prompt_toolkit.contrib.completers import WordCompleter as _WordCompleter
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory as _AutoSuggestFromHistory
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
            history = _FileHistory(history_filepath)

        self._history = history
        # NOTE: there's a sentence option here that might be interesting to explore
        self._completer = _WordCompleter([], ignore_case=True)
        self._suggest = _AutoSuggestFromHistory()

        def _get_prompt_tokens(*args):
            return [(_Token.Prompt, self.prompt)]

        def _get_rprompt_tokens(*args):
            return [(_Token.RPrompt, self._bot)]

        self.app = create_prompt_application(history=self._history,
                                             auto_suggest=_AutoSuggestFromHistory(),
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
        # profile = 'default'
        # name = self.command_manager._robot_name
        # return '{}[{}]: '.format(name, profile)
        return 'vexbot: '

    def cmdloop_and_start_messaging(self):
        self._thread.start()
        self.cmdloop()

    def cmdloop(self, intro=None):
        if intro is None:
            intro = "\nVexbot {}\n\n    Type \"!help\" for command line help or \"!commands\" for bot commands\n    \"!start bot\" will start up the bot.\n\n".format(__version__)
        print(intro, flush=True)
        while True:
            try:
                # FIXME
                if self._bot == self._NO_BOT:
                    self.command_manager.check_for_bot()
                    pass

                with self._patch_context:
                    result = self.cli.run(True)
                    text = result.text
                    text = self._clean_text(text)
                    if self.command_manager.is_command(result.text):
                        self.command_manager.handle_command(result.text)
                    else:
                        self.messaging.send_command(result.text)
            except EOFError:
                break
        self.eventloop.close()

    def _clean_text(self, text: str):
        text = text.lstrip()
        return text

    def run(self):
        while True:
            for msg in self.messaging.run():
                if msg.type == 'RSP':
                    self._handle_response(msg)

    def _handle_response(self, message):
        header = message.contents.get('original', 'Response')
        contents = message.contents.get('response', None)
        pprint.pprint(contents, compact=True)

    def set_bot_prompt_no(self):
        self._bot = self._NO_BOT
        self.cli.request_redraw()

    def set_bot_prompt_yes(self, *args, **kwargs):
        self._bot = ''
        self.cli.request_redraw()
