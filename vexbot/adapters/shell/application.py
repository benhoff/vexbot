import sys
from threading import Thread as _Thread

from prompt_toolkit.shortcuts import Prompt
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.output import create_output

from vexbot import __version__
from vexbot.adapters.messaging import Messaging as _Messaging
from vexbot.adapters.scheduler import Scheduler
from vexbot.adapters.shell.observers import PrintObserver, CommandObserver

class Shell(Prompt):
    def __init__(self,
                 messaging=None,
                 history_filepath=None,
                 display_help=True):

        self.messaging = messaging or _Messaging('shell')
        self._messaging_scheduler = Scheduler(self.messaging)
        self._messaging_scheduler.subscribe.subscribe(PrintObserver())
        self._thread = _Thread(target=self._messaging_scheduler.run, daemon=True)
        self.running = False


        # NOTE: the command observer is currently NOT hooked up to the
        # scheduler
        self.command_observer = CommandObserver(self.messaging)
        super().__init__(message='vexbot: ',
                         enable_history_search=True,
                         enable_system_prompt=True,
                         enable_suspend=True,
                         enable_open_in_editor=True)

    def run(self):
        self._thread.start()
        with patch_stdout():
            while True:
                try:
                    text = self.prompt()
                except EOFError:
                    return

                text = text.text.lstrip()
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
