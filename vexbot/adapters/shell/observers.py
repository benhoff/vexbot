import sys as _sys
from time import localtime, strftime
from random import randrange
import inspect
import logging
import pprint

from tblib import Traceback
from prompt_toolkit.styles import Attrs

from vexmessage import Message, Request

from vexbot.observer import Observer
from vexbot.intents import intent
from vexbot.command import command
from vexbot.util.lru_cache import LRUCache as _LRUCache
from vexbot.extensions import (subprocess,
                               hidden,
                               log,
                               develop,
                               admin)

try:
    from vexbot.subprocess_manager import SubprocessManager
# FIXME: Need to log here
except ImportError:
    SubprocessManager = None


def _get_attributes(output, color: str):
    attr = Attrs(color=color, bgcolor='', bold=False, underline=False,
                 italic=False, blink=False, reverse=False)
    if output.true_color() and not output.ansi_colors_only():
        return output._escape_code_cache_true_color[attr]
    else:
        return output._escape_code_cache[attr]


class CommandObserver(Observer):
    extensions = (subprocess.start,
                  subprocess.stop,
                  subprocess.restart,
                  subprocess.status,
                  log.debug,
                  # log.set_log_info,
                  develop.get_members,
                  develop.get_code,
                  admin.disable,
                  admin.enable,
                  admin.get_disabled,
                  admin.update,
                  admin.install,
                  admin.update)

    def __init__(self,
                 messaging,
                 prompt=None):

        super().__init__()
        if SubprocessManager is not None:
            self.subprocess_manager = SubprocessManager()
        else:
            self.subprocess_manager = None

        self._prompt = prompt
        self.messaging = messaging
        # Get the root logger to set it to different levels
        self._root = logging.getLogger()
        self.logger = logging.getLogger(__name__)

        self._bot_callback = None
        self._no_bot_callback = None
        self._commands = {}
        self._disabled = {}
        for name, method in inspect.getmembers(self):
            if name.startswith('do_'):
                self._commands[name[3:]] = method
            elif getattr(method, 'command', False):
                self._commands[name] = method
            else:
                continue

            if getattr(method,  'alias', False):
                for alias in method.alias:
                    self._commands[alias] = method

    @intent(name='stop_chatter')
    def do_stop_print(self, *args, **kwargs):
        self._prompt._print_subscription.dispose()

    def is_command(self, command: str) -> bool:
        return command in self._commands

    @intent(name='start_chatter')
    def do_start_print(self, *args, **kwargs):
        if not self._prompt._print_subscription.is_disposed:
            return

        # alias out for santity
        sub = self._prompt._messaging_scheduler.subscribe
        self._prompt._print_subscription = sub.subscribe(self._prompt.print_observer)

    def on_error(self, error: Exception, text: str, *args, **kwargs):
        _, value, _ = _sys.exc_info()
        print('{}: {}'.format(value.__class__.__name__, value))

    def do_help(self, *arg, **kwargs):
        """
        Help helps you figure out what commands do.
        Example usage: !help code
        To see all commands: !commands
        """
        try:
            name = arg[0]
        except IndexError:
            return 'welcome to vexbot! !commands will list all availabe commands'
        if any([name.startswith(x) for x in self._prompt.shebangs]):
            name = name[1:]
        try:
            callback = self._commands[name]
        except KeyError:
            self.logger.info(' !help not found for: %s', name)
            return self.do_help.__doc__

        return callback.__doc__

    # @command(alias=['warn'], hidden=True)
    def do_logging_default(self, *args, **kwargs):
        self._root.setLevel(logging.WARN)

    def do_hidden(self, *args, **kwargs):
        results = []
        for k, v in self._commands.items():
            if hasattr(v, 'hidden') and v.hidden:
                results.append('!' + k)
            else:
                continue
        return results

    def on_completed(self, *args, **kwargs):
        pass

    def on_next(self, request: Request):
        # NOTE: these are the responses to our commands
        result = request.kwargs.get('result')
        if result is None:
            return

        if request.kwargs.get('suppress'):
            return

        if isinstance(result, str):
            print(result)
        else:
            pprint.pprint(result)

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
        return tuple(self._prompt.author_interface.authors.keys())

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

    # @command(alias=['quit',])
    def do_exit(self, *args, **kwargs):
        _sys.exit(0)

    def do_history(self, *args, **kwargs) -> list:
        if self._prompt:
            return self._prompt.history.strings[-15:]
    
    def do_autosuggestions(self, *args, **kwargs):
        if self._prompt:
            return self._prompt._word_completer.words

    def handle_command(self, command, *args, **kwargs):
        try:
            callback = self._commands[command]
        except KeyError:
            return

        result = callback(*args, **kwargs)
        return result

    def do_services(self, *args, **kwargs) -> list:
        return self._prompt.service_interface.services

    def do_filter(self, *args, **kwargs):
        if not args:
            raise ValueError('Must supply something to filter against!')
        for name in args:
            for handler in self._root.handlers:
                handler.addFilter(logging.Filter(name))

    def do_anti_filter(self, *args, **kwargs):
        def filter_(record: logging.LogRecord):
            if record.name in args:
                return False
            return True
        for handler in self._root.handlers:
            handler.addFilter(filter_)

    def do_channels(self, *args, **kwargs) -> tuple:
        return tuple(self._prompt.service_interface.channels.keys())

    def do_time(sef, *args, **kwargs) -> str:
        time_format = "%H:%M:%S"
        time = strftime(time_format, localtime())
        return time

    @command(alias=['get_commands'])
    def do_commands(self, *args, **kwargs) -> list:
        commands = self._get_commands()
        return sorted(commands, key=str.lower)

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
        self._time_format = "%H:%M"

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
    def __init__(self, interface):
        super().__init__()
        self.interface = interface

    def on_next(self, msg: Message):
        source = msg.source
        channel = msg.contents.get('channel')
        self.interface.add_service(source, channel)

    def on_error(self, *args, **kwargs):
        pass

    def on_completed(self, *args, **kwargs):
        pass


class LogObserver(Observer):
    def __init__(self, logger: logging.Logger=None, pass_through=False):
        super().__init__()
        if logger is None:
            logger = logging.getLogger()
        self.root = logger
        self.passthrough = pass_through
        self.logger = logging.getLogger(__name__ + '.log')

    def on_next(self, msg: Message):
        type_ = msg.contents.get('type')
        # self.logger.debug(' type: %s', type_)
        if type_ is None:
            return
        elif type_ != 'log':
            return
        # remove unused 'type' value
        msg.contents.pop('type')
        # NOTE: Fixes formatting issue used by logging lib, I.E. msg % args
        args = msg.contents['args']
        if isinstance(args, list):
            msg.contents['args'] = tuple(args)
        else:
            msg.contents['args'] = args

        exc_info = msg.contents['exc_info']
        # deserialize exc_info
        if exc_info:
            import traceback
            # FIXME 
            traceback.print_tb(Traceback.from_dict(exc_info).as_traceback())
            return
            # exc_info = (None, None, Traceback.from_dict(exc_info[2]).as_traceback())
            """
            new_exc_info = []
            # Exception type
            # FIXME: bad exception handeling
            try:
                type_ = globals()['__builtins__'][exc_info[0]]
                # pass in excption arguments
                value = type_(*exc_info[1])
                traceback = Traceback.from_dict(exc_info[2]).as_traceback()
                new_exc_info = [type_, value, traceback]
                msg.contents['exc_info'] = new_exc_info
            except KeyError:
                # FIXME 
                pass
            """

            # overwrite the member

        record = logging.LogRecord(**msg.contents)
        if self.passthrough:
            self.root.handle(record)
        else:
            if record.levelno >= self.root.level:
                self.root.handle(record)

    def on_error(self, *args, **kwargs):
        pass

    def on_completed(self, *args, **kwargs):
        pass


class AuthorObserver(Observer):
    def __init__(self, interface):
        super().__init__()
        self.interface = interface

    def on_next(self, msg: Message):
        if msg.contents.get('author') is not None:
            self.interface.add_author(source=msg.source, **msg.contents)

    def on_error(self, *args, **kwargs):
        return

    def on_completed(self, *args, **kwargs):
        return


class ServicesObserver(Observer):
    def __init__(self, set_services_callback, set_command_callback):
        super().__init__()
        self.services_callback = set_services_callback
        self.command_callback = set_command_callback

    def on_next(self, request: Request):
        command = request.command
        if command not in ('services', 'get_commands'):
            return
        result = request.kwargs['result']
        if result is None:
            return
        if command == 'services':
            self.services_callback(result)
        elif command == 'get_commands':
            service = request.kwargs.get('service')
            if service is None:
                # FIXME: LOG ERROR
                return
            self.command_callback(service, result)

    def on_error(self, *args, **kwargs):
        pass

    def on_completed(self, *args, **kwargs):
        pass
