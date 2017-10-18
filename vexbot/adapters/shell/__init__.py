from os import path
import shlex as _shlex
import pprint as _pprint
from threading import Thread as _Thread

from prompt_toolkit.shortcuts import Prompt
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.history import FileHistory
from prompt_toolkit.shortcuts import CompleteStyle
from prompt_toolkit.contrib.completers import WordCompleter

from vexbot.adapters.messaging import Messaging as _Messaging
from vexbot.adapters.scheduler import Scheduler
from vexbot.adapters.shell.parser import parse
from vexbot.util.get_vexdir_filepath import get_vexdir_filepath

from vexbot.adapters.shell._lru_cache import _LRUCache
from vexbot.adapters.shell.observers import (PrintObserver,
                                             CommandObserver,
                                             AuthorObserver,
                                             ServiceObserver)


def _super_parse(string: str) -> (list, dict):
    """
    turns a shebang'd string into a list and dict, i.e. (args, kwargs)
    List and dict may be empty
    """
    string = string[1:]
    args = _shlex.split(string)
    try:
        command = args.pop(0)
    except IndexError:
        return [], {}
    args, kwargs = parse(args)
    return args, kwargs


def _get_command(arg: str) -> str:
    # consume shebang
    arg = arg[1:]
    # Not sure if `shlex` can handle unicode. If can, this can be done
    # here rather than having a helper method
    args = _shlex.split(arg)
    try:
        return args.pop(0)
    except IndexError:
        return


class Shell(Prompt):
    def __init__(self,
                 messaging=None,
                 history_filepath=None,
                 display_help=True):

        self.messaging = messaging or _Messaging('shell', run_control_loop=True)
        self._messaging_scheduler = self.messaging.scheduler
        self._thread = _Thread(target=self._messaging_scheduler.loop.start,
                               daemon=True)

        self.shebangs = ['!', ]
        self.running = False

        # NOTE: the command observer is currently NOT hooked up to the
        # scheduler
        self.command_observer = CommandObserver(self.messaging, prompt=self)
        if history_filepath is None:
            vexdir = get_vexdir_filepath()
            history_filepath = path.join(vexdir, 'vexshell_history')

        self.history = FileHistory(history_filepath)
        commands = self.command_observer._get_commands()
        self._word_completer = WordCompleter(commands)
        super().__init__(message='vexbot: ',
                         enable_system_prompt=True,
                         enable_suspend=True,
                         enable_open_in_editor=True,
                         history=self.history,
                         complete_while_typing=False,
                         completer=self._word_completer)

        def add_author(author):
            self._word_completer.words.append(author)

        def remove_author(author):
            try:
                self._word_completer.words.remove(author)
            except Exception:
                pass

        self.print_observer = PrintObserver(self.app)
        self.author_observer = AuthorObserver(add_author, remove_author)
        self.service_observer = ServiceObserver(self.messaging)

        self._print_subscription = self._messaging_scheduler.subscribe.subscribe(self.print_observer)
        self._messaging_scheduler.subscribe.subscribe(self.author_observer)
        self._messaging_scheduler.subscribe.subscribe(self.service_observer)

    def is_command(self, text: str) -> bool:
        """
        checks for presence of shebang in the first character of the text
        """
        if text[0] in self.shebangs:
            return True

        return False

    def _handle_service(self, service: str, *args, **kwargs):
        args = list(args)
        try:
            command = args.pop(0)
        except IndexError:
            return

        if self.is_command(command):
            # consume shebang
            command = command[1:]
        else:
            command = 'MSG'

        try:
            self.service_observer.handle_command(service, command, *args, **kwargs)
        except Exception as e:
            self.service_observer.on_error(e, command)

    def _handle_command(self, text: str):
        command = _get_command(text)
        if command is None:
            return
        # TODO: Verify that this correctly consumes the command
        args, kwargs = _super_parse(text)
        if self.command_observer.is_command(command):
            try:
                return self.command_observer.handle_command(command, *args, **kwargs)
            except Exception as e:
                self.command_observer.on_error(e, text)
                return
        elif self.service_observer.is_command(command):
            return self._handle_service(command, *args, **kwargs)

    def _handle_author_command(self, string: str, author: str, source: str, metadata: dict=None):
        command = _get_command(string)
        if command is None:
            return

        args, kwargs = _super_parse(string)
        # Update the metadata with any command line args
        if metadata is not None:
            metadata.update(kwargs)
            kwargs = metadata

        kwargs['msg_target'] = author
        if not kwargs.get('force-remote'):
            try:
                callback = self.command_observer._commands[command]
            except KeyError:
                self.messaging.send_command(command,
                                            *args,
                                            target=source,
                                            **kwargs)

                return

            result = callback(args, kwargs)
            if result:
                message = _pprint.pformat(result)
                self.messaging.send_command('MSG', target=source, message=message)

    def _handle_author(self, text: str):
        author = text.split(' ', 1)
        if len(author) < 2:
            return

        string = author[1]
        author = author[0]

        if author in self.author_observer.authors:
            source = self.author_observer.authors[author]
            metadata = self.author_observer.author_metadata[author]
            # check for shebang
            if self.is_command(string):
                return self._handle_author_command(string, author, source, metadata)
            else:
                self.messaging.send_command('MSG', target=source, message=string, msg_target=author, **metadata)

    def run(self):
        self._thread.start()
        with patch_stdout(raw=True):
            while True:
                try:
                    text = self.prompt()
                except KeyboardInterrupt:
                    continue
                except EOFError:
                    return

                if text == '':
                    continue
                text = text.lstrip()
                if self.is_command(text):
                    result = self._handle_command(text)

                    if result:
                        _pprint.pprint(result)
                        continue

                    continue
                self._handle_author(text)
