import re
from os import path
import shlex as _shlex
import pprint as _pprint
from threading import Thread as _Thread

from prompt_toolkit.shortcuts import Prompt
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.history import FileHistory
from prompt_toolkit.shortcuts import CompleteStyle
from prompt_toolkit.contrib.completers import WordCompleter
from prompt_toolkit.document import _FIND_CURRENT_WORD_INCLUDE_TRAILING_WHITESPACE_RE

from vexbot.adapters.messaging import Messaging as _Messaging
from vexbot.adapters.shell.parser import parse
from vexbot.util.get_vexdir_filepath import get_vexdir_filepath

from vexbot.adapters.shell._lru_cache import _LRUCache
from vexbot.adapters.shell.observers import (PrintObserver,
                                             CommandObserver,
                                             AuthorObserver,
                                             ServiceObserver)


# add in ! and # to our word completion regex
_WORD = re.compile(r'([!#a-zA-Z0-9_]+|[^!#a-zA-Z0-9_\s]+)')


def _get_cmd_args_kwargs(text: str) -> (str, tuple, dict):
    # consume shebang
    text = text[1:]
    args = _shlex.split(text)
    try:
        command = args.pop(0)
    except IndexError:
        return '', (), {}
    args, kwargs = parse(args)
    return command, args, kwargs


def _get_default_history_filepath():
    vexdir = get_vexdir_filepath()
    return path.join(vexdir, 'vexshell_history')


class Shell(Prompt):
    def __init__(self, history_filepath=None):
        if history_filepath is None:
            history_filepath = _get_default_history_filepath()

        self.history = FileHistory(history_filepath)
        self.messaging = _Messaging('shell', run_control_loop=True)

        # NOTE: should be able to get rid of these lines with a cleaner api
        self._thread = _Thread(target=self.messaging.start,
                               daemon=True)

        self.shebangs = ['!', ]

        # NOTE: the command observer is currently NOT hooked up to the
        # scheduler
        self.command_observer = CommandObserver(self.messaging, prompt=self)

        commands = self.command_observer._get_commands()
        self._word_completer = WordCompleter(commands, WORD=_WORD)

        super().__init__(message='vexbot: ',
                         history=self.history,
                         completer=self._word_completer,
                         enable_system_prompt=True,
                         enable_suspend=True,
                         enable_open_in_editor=True,
                         complete_while_typing=False)

        # NOTE: This method is used to add words to the word completer
        def add_word(word: str):
            self._word_completer.words.append(word)

        # NOTE: This method is used to add words to the word completer
        def remove_word(word: str):
            try:
                self._word_completer.words.remove(word)
            except Exception:
                pass

        self.print_observer = PrintObserver(self.app)
        self.author_observer = AuthorObserver(add_word, remove_word)
        self.service_observer = ServiceObserver(add_word, remove_word)

        self._print_subscription = self.messaging.chatter.subscribe(self.print_observer)
        self.messaging.chatter.subscribe(self.author_observer)
        self.messaging.chatter.subscribe(self.service_observer)

    def is_command(self, text: str) -> bool:
        """
        checks for presence of shebang in the first character of the text
        """
        if text[0] in self.shebangs:
            return True

        return False

    def run(self):
        self._thread.start()
        with patch_stdout(raw=True):
            while True:
                # Get our text
                try:
                    text = self.prompt()
                # KeyboardInterrupt continues
                except KeyboardInterrupt:
                    continue
                # End of file returns
                except EOFError:
                    return

                # Clean text
                text = text.lstrip()
                # Handle empty text
                if text == '':
                    continue
                # Program specific handeling. Currently either first word
                # or second word can be commands
                self._handle_text(text)

    def _handle_text(self, text: str):
        """
        Check to see if text is a command. Otherwise, check to see if the
        second word is a command.

        Commands get handeled by the `_handle_command` method

        If not command, check to see if first word is a service or an author.
        Default program is to send message replies. However, we will also
        check to see if the second word is a command and handle approparitly

        This method does simple string parsing and high level program control
        """
        # If first word is command
        if self.is_command(text):
            # get the command, args, and kwargs out using `shlex`
            command, args, kwargs = _get_cmd_args_kwargs(text)
            # hand off to the `handle_command` method
            result = self._handle_command(command, args, kwargs)

            if result:
                # print our results
                _pprint.pprint(result)
            # Exit the method here if in this block
            return
        # Else check if second word is a command
        else:
            # get the first word and then the rest of the text. Text reassign
            # here
            try:
                first_word, text = text.split(' ', 1)
            except ValueError:
                return
            # check if second word/string is a command
            if self.is_command(text):
                # get the command, args, and kwargs out using `shlex`
                command, args, kwargs = _get_cmd_args_kwargs(text)
            # if second word is not a command, default to message
            else:
                command = 'MSG'
                args = ()
                kwargs = {'message': text}

            # since we've defaulted to message if not command, this api makes
            # sense for now. If we don't default to message, need to refactor
            self._first_word_not_cmd(first_word, command, args, kwargs)

    def _handle_command(self, command: str, args: tuple, kwargs: dict):
        # TODO: Command fallthrough to bot? Currently just sees if command local
        # and exits if not
        if self.command_observer.is_command(command):
            try:
                return self.command_observer.handle_command(command, *args, **kwargs)
            except Exception as e:
                self.command_observer.on_error(e, command, args, kwargs)
                return

    def _first_word_not_cmd(self,
                            first_word: str,
                            command: str,
                            args: tuple,
                            kwargs: dict) -> None:
        """
        check to see if this is an author or service.
        This method does high level control handling
        """
        if self.service_observer.is_service(first_word):
            args, kwargs = self._handle_service(first_word, args, kwargs)
        elif self._is_author(first_word):
            args, kwargs = self._handle_author(first_word, args, kwargs)
        if not kwargs.get('force-remote'):
            try:
                callback = self.command_observer._commands[command]
            except KeyError:
                kwargs['remote_command'] = command
                command= 'CMD'
                self.messaging.send_command(command, *args, **kwargs)
                return
            try:
                result = callback(*args, **kwargs)
            except Exception as e:
                self.command_observer.on_error(e, command)
                return

            if result:
                message = _pprint.pformat(result)
                self.messaging.send_command('MSG', message=message, *args, **kwargs)
        else:
            self.messaging.send_command(command, *args, **kwargs)

    def _handle_service(self,
                        service: str,
                        args: tuple,
                        kwargs: dict) -> (str, tuple, dict):
        return self.service_observer.handle_command(service, args, kwargs)

    def _is_author(self, author: str):
        return author in self.author_observer.authors

    def _handle_author(self, author: str, args: tuple, kwargs: dict) -> (tuple, dict):
        source = self.author_observer.authors[author]
        metadata = self.author_observer.author_metadata[author]
        metadata.update(kwargs)
        kwargs = metadata
        kwargs['target'] = source
        kwargs['msg_target'] = author
        return args, kwargs
