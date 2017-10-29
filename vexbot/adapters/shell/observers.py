import sys as _sys
import functools
from time import localtime, strftime
from random import randrange
import inspect
import logging

from rx import Observer

from prompt_toolkit.styles import Attrs

from vexmessage import Message

from vexbot.util.lru_cache import LRUCache as _LRUCache
from vexbot.subprocess_manager import SubprocessManager


def _get_attributes(output, color: str):
    attr = Attrs(color=color, bgcolor='', bold=False, underline=False,
                 italic=False, blink=False, reverse=False)
    if output.true_color() and not output.ansi_colors_only():
        return output._escape_code_cache_true_color[attr]
    else:
        return output._escape_code_cache[attr]


# possible other args: Name
def shellcommand(function=None,
                 alias: list=None,
                 hidden: bool=False):
    if function is None:
        return functools.partial(shellcommand,
                                 alias=alias,
                                 hidden=hidden)

    # https://stackoverflow.com/questions/10176226/how-to-pass-extra-arguments-to-python-decorator
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        return function(*args, **kwargs)
    # TODO: check for string and convert to list
    if alias is not None:
        wrapper.alias = alias

    wrapper.hidden = hidden

    return wrapper


_LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'


class CommandObserver(Observer):
    def __init__(self,
                 messaging,
                 prompt=None):

        self.subprocess_manager = SubprocessManager()
        self._prompt = prompt
        self.messaging = messaging
        # Get the root logger to set it to different levels
        self._root = logging.getLogger()

        self._logger = logging.getLogger(__name__)

        self._bot_callback = None
        self._no_bot_callback = None
        self._commands = {}
        for method in dir(self):
            if method.startswith('do_'):
                method_obj = getattr(self, method)
                self._commands[method[3:]] = method_obj
                try:
                    for alias in method_obj.alias:
                        self._commands[alias] = method_obj
                except AttributeError:
                    continue

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

    @shellcommand(hidden=True)
    def do_debug(self, *args, **kwargs):
        # FIXME: I'm not sure that I need to set the basicConfig everytime
        logging.basicConfig(level=logging.DEBUG, format=_LOG_FORMAT)
        self._root.setLevel(logging.DEBUG)

    @shellcommand(hidden=True)
    def do_info(self, *args, **kwargs):
        logging.basicConfig(level=logging.INFO, format=_LOG_FORMAT)
        self._root.setLevel(logging.INFO)

    @shellcommand(alias=['warn'], hidden=True)
    def do_logging_default(self, *args, **kwargs):
        logging.basicConfig(level=logging.WARN, format=_LOG_FORMAT)
        self._root.setLevel(logging.WARN)

    def on_completed(self, *args, **kwargs):
        pass

    def on_next(self, *args, **kwargs):
        pass

    def do_help(self, *arg, **kwargs):
        """
        Help helps you figure out what commands do.
        Example usage: !help code
        To see all commands: !commands
        """
        name = arg[0]
        self._prompt.shebangs
        if any([name.startswith(x) for x in self._prompt.shebangs]):
            name = name[1:]
        try:
            callback = self._commands[name]
        except KeyError:
            self._logger.info(' !help not found for: %s', name)
            return self.do_help.__doc__

        return callback.__doc__

    def set_on_bot_callback(self, callback):
        self._bot_callback = callback

    def set_no_bot_callback(self, callback):
        self._no_bot_callback = callback

    def do_subscribe(self, *args, **kwargs):
        """
        Subscribe to a publish port. Example:
        `vexbot: !subscribe tcp://127.0.0.1:3000`
        """
        for address in args:
            try:
                self.messaging.subscription_socket.connect(address)
            except Exception:
                raise RuntimeError('addresses need to be in the form of: tcp://address_here:port_number'
                                   ' example: tcp://10.2.3.4:80'
                                   'address tried {}'.format(address))

    def do_authors(self, *args, **kwargs) -> tuple:
        return tuple(self._prompt.author_observer.authors.keys())

    def do_color(self, *args, **kwargs):
        author = None
        try:
            author = args[0]
        except IndexError:
            pass
        if author is None:
            author = kwargs.get('msg_target')
        if author is None:
            return

        if self._prompt.print_observer:
            del self._prompt.print_observer._author_color[author]

    @shellcommand(alias=['quit',])
    def do_exit(self, *args, **kwargs):
        _sys.exit(0)

    def do_ping(self, *args, **kwargs):
        self.messaging.send_ping()

    def do_history(self, *args, **kwargs) -> list:
        if self._prompt:
            return self._prompt.history.strings

    @shellcommand(alias=['source',])
    def do_code(self, *args, **kwargs):
        """
        get the python source code from callback
        """
        try:
            callback = self._commands[args[0]]
        except (IndexError, KeyError):
            return
        source = inspect.getsourcelines(callback)
        # FIXME: formatting sucks
        return "\n" + "".join(source[0])

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

    def do_start(self, target: str, *args, **kwargs):
        mode = kwargs.get('mode', 'replace')
        # TODO: Better aliasing for more commands
        if target == 'bot':
            target = 'vexbot'

        self.subprocess_manager.start(target, mode)

    def do_status(self, target: str=None, *args, **kwargs):
        if target is None:
            err = ('!status requires a target name to inquire about. Example'
                   ' usage: `!status vexbot.service`')
            raise RuntimeError(err)

        status = self.subprocess_manager.status(target)
        return status

    def do_services(self, *args, **kwargs) -> list:
        return self._prompt.service_observer.services

    def do_channels(self, *args, **kwargs) -> tuple:
        return tuple(self._prompt.service_observer.channels.keys())

    def do_restart(self, target: str=None, *args, **kwargs):
        if target is None:
            err = ('!restart requires a target name to inquire about. Example'
                   ' usage: `!restart vexbot.service`')
            raise RuntimeError(err)

        mode = kwargs.get('mode', 'replace')
        if target == 'bot':
            target = 'vexbot'

        self.subprocess_manager.restart(target, mode)

    def do_stop(self, target: str, *args, **kwargs):
        mode = kwargs.get('mode', 'replace')
        if target == 'bot':
            target = 'vexbot'

        self.subprocess_manager.stop(target, mode)

    def do_time(sef, *args, **kwargs) -> str:
        time_format = "%H:%M:%S"
        time = strftime(time_format, localtime())
        return time

    def do_commands(self, *args, **kwargs) -> list:
        commands = self._get_commands()
        return commands

    def _get_commands(self) -> list:
        results = []
        for k, v in self._commands.items():
            if hasattr(v, 'hidden') and v.hidden:
                continue
            else:
                results.append('!' + k)
        return results


class PrintObserver(Observer):
    def __init__(self, application=None):
        super().__init__()
        # NOTE: if this raises an error, then the instantion is incorrect.
        # Need to instantiate the application before the print observer
        output = application.output

        colors = ('af8700', '5f5faf', '0087ff', '2aa198', '5f8700')
        self.colors = [_get_attributes(output, color) for color in colors]
        self._grey = _get_attributes(output, 'ansidarkgray')
        self.num_colors = len(self.colors)

        self._author_color = _LRUCache(100)
        # NOTE: vt100 ONLY
        self._reset_color = '\033[0m'
        self._time_format = "%H:%M:%S"

    def _get_author_color(self, author: str):
        # NOTE: This replace mocks the current behavior in the print observer
        author = author.replace(' ', '_')
        if author in self._author_color:
            author_color = self._author_color[author]
        else:
            author_color = self.colors[randrange(self.num_colors)]
            self._author_color[author] = author_color

        return author_color

    def on_next(self, msg: Message):
        author = msg.contents.get('author')
        if author is None:
            return

        author_color = self._get_author_color(author)

        # Get channel name or default to source
        channel = msg.contents.get('channel', msg.source)
        author = '{} {}: '.format(author, channel)
        message = msg.contents['message']
        time = strftime(self._time_format, localtime()) + ' '

        print(self._grey + time + author_color + author + self._reset_color + message)

    def on_error(self, *args, **kwargs):
        pass

    def on_completed(self, *args, **kwargs):
        pass


class ServiceObserver(Observer):
    def __init__(self, add_callback=None, remove_callback=None):
        super().__init__()
        self.services = set()
        self.channels = _LRUCache(100, add_callback, remove_callback)
        self._add_callback = add_callback

    def on_next(self, msg: Message):
        source = msg.source
        if source not in self.services and self._add_callback:
            self._add_callback(source)
        self.services.add(source)
        channel = msg.contents.get('channel')

        if channel:
            self.channels[channel] = source

    def on_error(self, *args, **kwargs):
        print(args, kwargs)

    def on_completed(self, *args, **kwargs):
        pass

    def is_service(self, service: str):
        in_service = service in self.services
        in_channel = service in self.channels
        return in_service or in_channel

    # FIXME: this API is brutal
    def handle_command(self, service: str, args: tuple, kwargs: dict) -> (str, tuple, dict):
        if service in self.channels:
            kwargs['channel'] = service
            service = self.channels[service]
        kwargs['target'] = service
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

        # NOTE: this fixes the parsing for usernames
        author = author.replace(' ', '_')

        self.authors[author] = msg.source
        self.author_metadata[author] = {k: v for k, v in msg.contents.items()
                                        if k in self.metadata_words} 

    def on_error(self, *args, **kwargs):
        return

    def on_completed(self, *args, **kwargs):
        return
