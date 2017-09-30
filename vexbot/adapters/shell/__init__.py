from threading import Thread as _Thread

from prompt_toolkit.shortcuts import Prompt
from prompt_toolkit.patch_stdout import patch_stdout

from vexbot.adapters.messaging import Messaging as _Messaging
from vexbot.adapters.scheduler import Scheduler
from vexbot.adapters.shell.observers import PrintObserver, CommandObserver


class Shell(Prompt):
    def __init__(self,
                 messaging=None,
                 history_filepath=None,
                 display_help=True):

        self.messaging = messaging or _Messaging('shell', run_control_loop=True)
        self._messaging_scheduler = self.messaging.scheduler
        self._thread = _Thread(target=self._messaging_scheduler.loop.start,
                               daemon=True)

        self.running = False

        # NOTE: the command observer is currently NOT hooked up to the
        # scheduler
        self.command_observer = CommandObserver(self.messaging, prompt=self)
        super().__init__(message='vexbot: ',
                         enable_system_prompt=True,
                         enable_suspend=True,
                         enable_open_in_editor=True)

        def add_author(author):
            self.history.append(author)

        def remove_author(author):
            try:
                self.history.strings.remove(author)
            except Exception:
                pass

        self.print_observer = PrintObserver(self.app,
                                            add_author,
                                            remove_author)

        self._messaging_scheduler.subscribe.subscribe(self.print_observer)

    def _handle_command(self, text):
        if self.command_observer.is_command(text):
            try:
                return self.command_observer.handle_command(text)
            except Exception as e:
                self.command_observer.on_error(e, text)
                return
        else:
            self.messaging.send_command(text)

    def _handle_author(self, text: str):
        author = text.split(' ', 1)
        if len(author) < 2:
            return
        string = author[1]
        author = author[0]
        if author in self.print_observer.authors:
            pass

    def run(self):
        self._thread.start()
        with patch_stdout(raw=True):
            while True:
                try:
                    text = self.prompt()
                except EOFError:
                    return

                if text == '':
                    continue
                text = text.lstrip()
                result = self._handle_command(text)
                if result:
                    # TODO: determine if this is the best way to do this
                    print(result)
                    continue
                self._handle_author(text)
