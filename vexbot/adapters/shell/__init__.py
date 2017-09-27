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
from vexbot.adapters.scheduler import Scheduler
from vexbot.adapters.messaging import Messaging as _Messaging
from vexbot.adapters.shell.observers import PrintObserver, CommandObserver


VEXBOT_SETTINGS_NAME = 'vexbot_shell'


class PromptShell:
    _NO_BOT = '<no bot detected>'
    def __init__(self,
                 messaging=None,
                 history_filepath=None):

        self._bot = self._NO_BOT
        self.messaging = messaging or _Messaging('shell')
        self.command_observer = CommandObserver(self.messaging)
        self._messaging_scheduler = Scheduler(self.messaging)
        self._messaging_scheduler.subscribe.subscribe(PrintObserver())
        self._thread = _Thread(target=self._messaging_scheduler.run, daemon=True)
        self.running = False
        # Tries to snag the bot properties
        self._robot = None
        self._setup_bot_watch()

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

    def _setup_bot_watch(self):
        bus = self.command_observer.subprocess_manager.bus
        systemd = self.command_observer.subprocess_manager.systemd
        self._robot = bus.get(".systemd1", systemd.GetUnit('vexbot.service'))

        self._robot.onPropertiesChange = self._handle_bot_change

    def _handle_bot_change(self, *args, **kwargs):
        print(args, kwargs)

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
                with self._patch_context:
                    text = self.cli.run(True)
                    text = text.text
                    text = self._clean_text(text)
                    if self.command_observer.is_command(text):
                        try:
                            result = self.command_observer.handle_command(text)
                        except Exception as e:
                            self.command_observer.on_error(e, text)
                            continue
                    else:
                        result = self.messaging.send_command(text)

                    if result:
                        # TODO: determine if this is the best way to do this
                        print(result)

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
