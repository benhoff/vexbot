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

def _super_parse(string: str) -> [list, dict]:
    """
    turns a shebang'd string into a list and dict (args, kwargs)
    or returns `None`
    """
    string = string[1:]
    args = _shlex.split(string)
    try:
        command = args.pop(0)
    except IndexError:
        return [], {}
    args, kwargs = parse(args)
    return args, kwargs


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
        channel = msg.contents.get('channel')
        if channel is None:
            author = '{}: '.format(author)
        else:
            author = '{} [{}]: '.format(author, channel)
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

        self.shebangs = ['!', ]
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

    def is_command(self, text: str):
        """
        checks for presence of shebang in the first character of the text
        """
        if text[0] in self.shebangs:
            return True

        return False

    def do_stop_print(self, *args, **kwargs):
        try:
            self._prompt._messaging_scheduler.subscribe.observers.remove(self._prompt.print_observer)
        except ValueError:
            return

    def do_start_print(self, *args, **kwargs):
        # alias out for santity
        sub = self._prompt._messaging_scheduler.subscribe
        if self._prompt.print_observer not in sub.observers:
            sub.subscribe(self._prompt.print_observer)

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

    def do_authors(self, *args, **kwargs):
        return tuple(self._prompt.author_observer.authors.keys())

    def do_exit(self, *args, **kwargs):
        _sys.exit(0)

    def do_ping(self, *args, **kwargs):
        self.messaging.send_ping()

    def do_history(self, *args, **kwargs):
        if self._prompt:
            return self._prompt.history.strings

    def do_autosuggestions(self, *args, **kwargs):
        if self._prompt:
            return self._prompt._word_completer.words

    def _get_command(self, arg: str):
        # consume shebang
        arg = arg[1:]
        # Not sure if `shlex` can handle unicode. If can, this can be done
        # here rather than having a helper method
        args = _shlex.split(arg)
        try:
            return args.pop(0)
        except IndexError:
            return

    def handle_command(self, arg: str):
        command = self._get_command(arg)
        args, kwargs = _super_parse(arg)
        try:
            callback = self._commands[command]
        except KeyError:
            # TODO: Notify user of fallthrough?
            self.messaging.send_command(command, args=args, kwargs=kwargs)
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
            raise RuntimeError('!status requires a program name to inquire about. Example usage: `!status vexbot.service`')
        status = self.subprocess_manager.status(program)
        return status

    def do_restart(self, program: str, *args, **kwargs):
        mode = kwargs.get('mode', 'replace')
        if program == 'bot':
            program = 'vexbot'

        self.subprocess_manager.restart(program, mode)

    def do_stop(self, program: str, *args, **kwargs):
        mode = kwargs.get('mode', 'replace')
        if program == 'bot':
            program = 'vexbot'

        self.subprocess_manager.stop(program, mode)

    def do_commands(self, *args, **kwargs):
        commands = self._get_commands()
        return commands

    def _get_commands(self) -> list:
        return ['!' + x for x in self._commands.keys()]
