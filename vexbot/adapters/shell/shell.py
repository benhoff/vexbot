import re
import time
from os import path
import shlex as _shlex
import pprint as _pprint
import logging
from threading import Thread as _Thread

from prompt_toolkit.shortcuts import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.patch_stdout import patch_stdout
from zmq.eventloop.ioloop import PeriodicCallback

from vexbot.adapters.shell.parser import parse as _parse
from vexbot.adapters.messaging import Messaging as _Messaging
from vexbot.util.get_vexdir_filepath import get_vexdir_filepath
from vexbot.adapters.shell.interfaces import (AuthorInterface,
                                              ServiceInterface,
                                              EntityInterface)

from vexbot.adapters.shell.observers import (PrintObserver,
                                             CommandObserver,
                                             AuthorObserver,
                                             ServiceObserver,
                                             LogObserver,
                                             ServicesObserver)

from vexbot.adapters.shell.completers import ServiceCompleter, WordCompleter


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
    args, kwargs = _parse(args)
    return command, args, kwargs


def _get_default_history_filepath():
    vexdir = get_vexdir_filepath()
    return path.join(vexdir, 'vexshell_history')


class Shell(PromptSession):
    def __init__(self, history_filepath=None):
        self._logger = logging.getLogger(__name__)
        if history_filepath is None:
            self._logger.info(' getting default history filepath.')
            history_filepath = _get_default_history_filepath()

        self._logger.info(' history filepath %s', history_filepath)
        self.history = FileHistory(history_filepath)
        self.messaging = _Messaging('shell', run_control_loop=True)

        # TODO: Cleanup this API access
        self.messaging._heartbeat_reciever.identity_callback = self._identity_callback
        self._thread = _Thread(target=self.messaging.start,
                               daemon=True)

        self._bot_status_monitor = PeriodicCallback(self._monitor_bot_state,
                                                    1000,
                                                    self.messaging.loop)

        self.shebangs = ['!', ]
        self.command_observer = CommandObserver(self.messaging, prompt=self)
        commands = self.command_observer._get_commands()
        self._word_completer = WordCompleter(commands, WORD=_WORD)
        self._services_completer = ServiceCompleter(self._word_completer)
        self.author_interface = AuthorInterface(self._word_completer,
                                                self.messaging)

        self.service_interface = ServiceInterface(self._word_completer,
                                                   self.messaging)

        self.entity_interface = EntityInterface(self.author_interface,
                                                self.service_interface)

        self._bot_status = ''

        super().__init__(message='vexbot: ',
                         history=self.history,
                         completer=self._services_completer,
                         enable_system_prompt=True,
                         enable_suspend=True,
                         enable_open_in_editor=True,
                         complete_while_typing=False)


        self.print_observer = PrintObserver(self.app)

        self._print_subscription = self.messaging.chatter.subscribe(self.print_observer)
        self.messaging.chatter.subscribe(LogObserver())
        self.messaging.command.subscribe(self.command_observer)
        self.messaging.command.subscribe(ServicesObserver(self._identity_setter,
                                                          self._set_service_completion))

    def _identity_setter(self, services: list) -> None:
        try:
            services.remove(self.messaging._service_name)
        except ValueError:
            pass

        for service in services:
            self.service_interface.add_service(service)
            self.messaging.send_command('REMOTE',
                                        remote_command='commands',
                                        target=service,
                                        suppress=True)

    def _set_service_completion(self, service: str, commands: list) -> None:
        shebang = self.shebangs[0]
        commands = [shebang + command for command in commands]
        completer = WordCompleter(commands, WORD=_WORD)
        self._services_completer.set_service_completer(service, completer)

        # FIXME: `!commands` does not update these as it
        if service == 'vexbot':
            for command in commands:
                self._word_completer.words.add(command)

    def _identity_callback(self):
        self.messaging.send_command('services', suppress=True)
        self.messaging.send_command('get_commands', suppress=True)

    def _monitor_bot_state(self):
        time_now = time.time()
        last_message = self.messaging._heartbeat_reciever._last_message_time
        # TODO: put in a countdown since last contact?
        delta_time = time_now - last_message
        # NOTE: Bot is set to send a heartbeat every 1.5 seconds
        if time_now - last_message > 3.4:
            self._bot_status = '<NO BOT>'
        else:
            if self._bot_status == '':
                return
            self._bot_status = ''

        self.app.invalidate()

    def is_command(self, text: str) -> bool:
        """
        checks for presence of shebang in the first character of the text
        """
        if text[0] in self.shebangs:
            return True

        return False

    def run(self):
        self._thread.start()
        self._bot_status_monitor.start()
        with patch_stdout(raw=True):
            while True:
                # Get our text
                try:
                    text = self.prompt(rprompt=self._get_rprompt_tokens)
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
                    self._logger.debug(' empty string found')
                    continue
                # Program specific handeling. Currently either first word
                # or second word can be commands
                for string in text.split('&&'):
                    self._handle_text(string)

    def _get_rprompt_tokens(self):
        return self._bot_status

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
            self._logger.debug(' first word is a command')
            # get the command, args, and kwargs out using `shlex`
            command, args, kwargs = _get_cmd_args_kwargs(text)
            self._logger.info(' command: %s, %s %s', command, args, kwargs)
            # hand off to the `handle_command` method
            result = self._handle_command(command, args, kwargs)

            if result:
                if isinstance(result, str):
                    print(result)
                else:
                    _pprint.pprint(result)
            # Exit the method here if in this block
            return
        # Else first word is not a command
        else:
            self._logger.debug(' first word is not a command')
            # get the first word and then the rest of the text.
            try:
                first_word, second_word = text.split(' ', 1)
                self._logger.debug(' first word: %s', first_word)
            except ValueError:
                self._logger.debug('No second word in chain!')
                return self._handle_NLP(text)
            # check if second word/string is a command
            if self.is_command(second_word):
                self._logger.info(' second word is a command')
                # get the command, args, and kwargs out using `shlex`
                command, args, kwargs = _get_cmd_args_kwargs(second_word)
                self._logger.debug(' second word: %s', command)
                self._logger.debug(' command %s', command)
                self._logger.debug('args %s ', args)
                self._logger.debug('kwargs %s', kwargs)
                return self._first_word_not_cmd(first_word, command, args, kwargs)
            # if second word is not a command, default to NLP
            else:
                self._logger.info(' defaulting to message since second word '
                                  'isn\'t a command')

                return self._handle_NLP(text)

    def _handle_NLP(self, text: str):
        entities = self.entity_interface.get_entities(text)
        self.messaging.send_command('NLP', text=text, entities=entities)

    def _handle_command(self, command: str, args: tuple, kwargs: dict):
        if kwargs.get('remote', False):
            self._logger.debug(' `remote` in kwargs, sending command')
            self.messaging.send_command(command, *args, **kwargs)
            return
        if self.command_observer.is_command(command):
            self._logger.debug(' `%s` is a command', command)
            # try:
            return self.command_observer.handle_command(command, *args, **kwargs)
            """
            except Exception as e:
                self.command_observer.on_error(e, command, args, kwargs)
                return
            """
        else:
            self._logger.debug('command not found! Sending to bot')
            self.messaging.send_command(command, *args, **kwargs)

    def _first_word_not_cmd(self,
                            first_word: str,
                            command: str,
                            args: tuple,
                            kwargs: dict) -> None:
        """
        check to see if this is an author or service.
        This method does high level control handling
        """
        if self.service_interface.is_service(first_word):
            self._logger.debug(' first word is a service')
            kwargs = self.service_interface.get_metadata(first_word, kwargs)
            self._logger.debug(' service transform kwargs: %s', kwargs)
        elif self.author_interface.is_author(first_word):
            self._logger.debug(' first word is an author')
            kwargs = self.author_interface.get_metadata(first_word, kwargs)
            self._logger.debug(' author transform kwargs: %s', kwargs)
        if not kwargs.get('remote'):
            kwargs['remote_command'] = command
            command= 'REMOTE'
            self.messaging.send_command(command, *args, **kwargs)
            return
        else:
            self.messaging.send_command(command, *args, **kwargs)
