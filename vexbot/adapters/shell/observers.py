import sys as _sys
import shlex as _shlex
from time import gmtime, strftime

from gi._error import GError
from rx import Observer

from prompt_toolkit.styles import Attrs

from vexmessage import Message

from vexbot.adapters.shell.parser import parse
from vexbot.adapters.shell._lru_cache import _LRUCache
from vexbot.subprocess_manager import SubprocessManager


def _get_attributes(output, attrs):
    if output.true_color() and not output.ansi_colors_only():
        return output._escape_code_cache_true_color[attrs]
    else:
        return output._escape_code_cache[attrs]


class AuthorObserver(Observer):
    def __init__(self, add_callback=None, delete_callback=None):
        super().__init__()
        self.authors = _LRUCache(100, add_callback, delete_callback)
        self.author_metadata = _LRUCache(100)
        self.metadata_words = ['channel', ]

    def on_next(self, msg: Message):
        author = msg.contents.get('author')
        if author is None:
            return

        self.authors[author] = msg.source
        self.author_metadata[author] = {k: v for k, v in msg.contents.items()
                                        if k in self.metadata_words} 

    def on_error(self, *args, **kwargs):
        return

    def on_completed(self, *args, **kwargs):
        return


class ServiceObserver(Observer):
    def __init__(self, messaging):
        super().__init__()
        self.services = set()
        self.channels = _LRUCache(100)
        self.messaging = messaging

    def on_next(self, msg: Message):
        source = msg.source
        self.services.add(source)
        channel = msg.contents.get('channel')

        if channel:
            self.channels[channel] = source

    def on_error(self, *args, **kwargs):
        print(args, kwargs)

    def on_completed(self, *args, **kwargs):
        pass

    def is_command(self, service: str):
        in_service = service in self.services
        in_channel = service in self.channels
        return in_service or in_channel

    # FIXME: this API is brutal
    def handle_command(self, service: str, command: str, *args, **kwargs):
        if service in self.channels:
            service = self.channels[service]
        kwargs['target'] = service
        kwargs['remote_command'] = command
        self.messaging.send_command('CMD', *args, **kwargs)


class PrintObserver(Observer):
    def __init__(self, application=None):
        super().__init__()
        # NOTE: if this raises an error, then the instantion is incorrect.
        # Need to instantiate the application before the print observer
        output = application.output

        attr = Attrs(color='ansigreen', bgcolor='', bold=False,
                     underline=False, italic=False, blink=False,
                     reverse=False)

        self._author_color = _get_attributes(output, attr)
        # NOTE: vt100 ONLY
        self._reset_color = '\033[0m'
        self._time_format = "%H:%M:%S"

    def on_next(self, msg: Message):
        author = msg.contents.get('author')
        if author is None:
            return
        # Get channel name or default to source
        channel = msg.contents.get('channel', msg.source)
        author = '{} {}: '.format(author, channel)
        """
        message = textwrap.fill(msg.contents['message'],
                                subsequent_indent='    ')
        """
        message = msg.contents['message']
        time = strftime(self._time_format, gmtime()) + ' '

        print(time + self._author_color + author + self._reset_color + message)

    def on_error(self, *args, **kwargs):
        pass

    def on_completed(self, *args, **kwargs):
        pass



class CommandObserver(Observer):
    def __init__(self,
                 messaging,
                 prompt=None):

        self.subprocess_manager = SubprocessManager()
        self._prompt = prompt
        self.messaging = messaging
        self.messaging.start()

        self._bot_callback = None
        self._no_bot_callback = None
        self._commands = {}
        for method in dir(self):
            if method.startswith('do_'):
                self._commands[method[3:]] = getattr(self, method)

    def do_stop_print(self, *args, **kwargs):
        self._prompt._print_subscription.dispose()

    def is_command(self, command: str) -> bool:
        return command in self._commands

    def do_start_print(self, *args, **kwargs):
        if not self._prompt._print_subscription.is_disposed:
            return

        # alias out for santity
        sub = self._prompt._messaging_scheduler.subscribe
        self._prompt._print_subscription = sub.subscribe(self._prompt.print_observer)

    def on_error(self, error: Exception, text: str, *args, **kwargs):
        _, value, _ = _sys.exc_info()
        print('{}: {}'.format(value.__class__.__name__, value))


    def on_completed(self, *args, **kwargs):
        pass

    def on_next(self, *args, **kwargs):
        pass

    def set_on_bot_callback(self, callback):
        self._bot_callback = callback

    def set_no_bot_callback(self, callback):
        self._no_bot_callback = callback

    def do_quit(self, *args, **kwargs):
        _sys.exit(0)

    def do_authors(self, *args, **kwargs) -> tuple:
        return tuple(self._prompt.author_observer.authors.keys())

    def do_exit(self, *args, **kwargs):
        _sys.exit(0)

    def do_ping(self, *args, **kwargs):
        # FIXME: broken
        self.messaging.send_ping()

    def do_history(self, *args, **kwargs) -> list:
        if self._prompt:
            return self._prompt.history.strings

    def do_autosuggestions(self, *args, **kwargs):
        if self._prompt:
            return self._prompt._word_completer.words

    def handle_command(self, command, *args, **kwargs):
        try:
            callback = self._commands[command]
        except KeyError:
            # TODO: Notify user of fallthrough?
            self.messaging.send_command(command, *args, **kwargs)
            return

        result = callback(*args, **kwargs)
        return result

    def do_start(self, program: str, *args, **kwargs):
        mode = kwargs.get('mode', 'replace')
        # TODO: Better aliasing for more commands
        if program == 'bot':
            program = 'vexbot'

        self.subprocess_manager.start(program, mode)

    def do_status(self, program: str=None, *args, **kwargs):
        if program is None:
            err = ('!status requires a program name to inquire about. Example'
                   ' usage: `!status vexbot.service`')
            raise RuntimeError(err)

        status = self.subprocess_manager.status(program)
        return status

    def do_services(self, *args, **kwargs) -> list:
        return self._prompt.service_observer.services

    def do_restart(self, program: str=None, *args, **kwargs):
        if program is None:
            err = ('!restart requires a program name to inquire about. Example'
                   ' usage: `!restart vexbot.service`')
            raise RuntimeError(err)

        mode = kwargs.get('mode', 'replace')
        if program == 'bot':
            program = 'vexbot'

        self.subprocess_manager.restart(program, mode)

    def do_stop(self, program: str, *args, **kwargs):
        mode = kwargs.get('mode', 'replace')
        if program == 'bot':
            program = 'vexbot'

        self.subprocess_manager.stop(program, mode)

    def do_time(sef, *args, **kwargs) -> str:
        time_format = "%H:%M:%S"
        time = strftime(time_format, gmtime())
        return time

    def do_commands(self, *args, **kwargs) -> list:
        commands = self._get_commands()
        return commands

    def _get_commands(self) -> list:
        return ['!' + x for x in self._commands.keys()]
