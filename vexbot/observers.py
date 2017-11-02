import sys as _sys
import logging
import inspect as _inspect
import functools as _functools

from rx import Observer

from vexmessage import Request
from vexbot.messaging import Messaging


def vexcommand(function=None,
               alias: list=None,
               hidden: bool=False):
    if function is None:
        return _functools.partial(vexcommand,
                                  alias=alias,
                                  hidden=hidden)

    # https://stackoverflow.com/questions/10176226/how-to-pass-extra-arguments-to-python-decorator
    @_functools.wraps(function)
    def wrapper(*args, **kwargs):
        return function(*args, **kwargs)
    # TODO: check for string and convert to list
    if alias is not None:
        wrapper.alias = alias
    wrapper.hidden = hidden
    return wrapper


_SUBPROCESS_MANAGER = 'vexbot.subprocess_manager.SubprocessManager'


class CommandObserver(Observer):
    def __init__(self,
                 bot,
                 messaging: Messaging,
                 subprocess_manager: _SUBPROCESS_MANAGER):

        super().__init__()
        self.bot = bot
        self.messaging = messaging
        self.subprocess_manager = subprocess_manager
        self._commands = self._get_commands()
        self.logger = logging.getLogger(self.messaging._service_name + '.observers.command')

        self._root_logger = logging.getLogger()
        self._root_logger.setLevel(logging.DEBUG)
        logging.basicConfig()
        # self._root_logger.addHandler(self.messaging.pub_handler)

    def _get_commands(self) -> dict:
        result = {}
        for name, method in _inspect.getmembers(self):
            if name.startswith('do_'):
                result[name[3:]] = method
                try:
                    for alias in method.alias:
                        result[alias] = method
                except AttributeError:
                    continue

        return result

    @vexcommand(alias=['MSG',])
    def do_REMOTE(self, source: list, *args, **kwargs):
        try:
            target = kwargs.pop('target')
            self.logger.debug(' do_REMOTE target: %s', target)
            command = kwargs.pop('remote_command')
            self.logger.debug(' do_REMOTE command: %s', command)
        except KeyError:
            self.logger.debug(' do_REMOTE KeyError, %s %s', args, kwargs)
            return

        if target == self.messaging._service_name:
            warn = 'target for remote command is the bot itself! Returning the function'
            self.logger.warn(warn)
            return self._handle_command(command, source, *args, **kwargs)

        try:
            target = self.messaging._address_map[target]
        except KeyError:
            warn = ' Target %s, not found in addresses. Are you sure that %s sent an IDENT message?'
            self.logger.warn(warn, target, target)
            # NOTE: Bail here since there's no point in going forward
            return

        self.logger.info(' REMOTE %s, target: %s | %s, %s',
                         command, target, args, kwargs)

        source = target + source
        self.messaging.send_command_response(source,
                                             command,
                                             *args, 
                                             **kwargs)

    def do_IDENT(self, source, *args, **kwargs):
        service_name = kwargs.get('service_name')
        if service_name is None:
            warn = (' No service name found for IDENT command. Not '
                    'identifying due to lack of human readable string! %s %s %s')
            self.logger.warn(warn, source, args, kwargs)
            return

        self.logger.info(' IDENT %s as %s', service_name, source)
        self.messaging._address_map[service_name] = source

    def do_log_level(self, *args, **kwargs):
        if not args:
            return self._root_logger.getEffectiveLevel()
        value = args[0]
        try:
            value = int(value)
        except ValueError:
            pass

        self._root_logger.setLevel(value)

    def do_services(self, *args, **kwargs):
        return tuple(self.messaging._address_map.keys())

    def do_help(self, *arg, **kwargs):
        """
        Help helps you figure out what commands do.
        Example usage: !help code
        To see all commands: !commands
        """
        name = arg[0]
        try:
            callback = self._commands[name]
        except KeyError:
            self._logger.info(' !help not found for: %s', name)
            return self.do_help.__doc__

        return callback.__doc__

    def do_debug(self, *args, **kwargs):
        self._root_logger.setLevel(logging.DEBUG)
        self.messaging.pub_handler.setLevel(logging.DEBUG)

    @vexcommand(alias=['source',])
    def do_code(self, *args, **kwargs):
        """
        get the python source code from callback
        """
        try:
            callback = self._commands[args[0]]
        except (IndexError, KeyError):
            return
        # TODO: syntax color would be nice
        source = _inspect.getsourcelines(callback)
        # FIXME: formatting sucks
        return "\n" + "".join(source[0])

    def do_warn(self, *args, **kwargs):
        self._root_logger.setLevel(logging.WARN)
        self.messaging.pub_handler.setLevel(logging.WARN)

    def do_info(self, *args, **kwargs) -> None:
        self._root_logger.setLevel(logging.INFO)
        self.messaging.pub_handler.setLevel(logging.INFO)

    def do_start(self, name: str, mode: str='replace', *args, **kwargs):
        self.logger.info(' start service %s in mode %s', name, mode)
        self.subprocess_manager.start(name, mode)

    def do_commands(self, *args, **kwargs):
        commands = tuple(self._commands.keys())
        return commands

    def do_restart(self, name: str, mode: str='replace', *args, **kwargs):
        self.logger.info(' restart service %s in mode %s', name, mode)
        self.subprocess_manager.restart(name, mode)

    def do_stop(self, name: str, mode: str='replace', *args, **kwargs):
        self.logger.info(' stop service %s in mode %s', name, mode)
        self.subprocess_manager.stop(name, mode)

    def _handle_result(self, command: str, source: list, result, *args, **kwargs):
        self.logger.info('send response %s %s %s', source, command, result)
        self.messaging.send_command_response(source, command, result=result, *args, **kwargs)

    def _handle_command(self,
                        command: str,
                        source: list,
                        *args,
                        **kwargs) -> None:

        try:
            callback = self._commands[command]
        except KeyError:
            self.logger.info(' command not found! %s', command)
            return

        self.logger.debug(' handle_command kwargs: %s', kwargs)
        kwargs['source'] = source
        try:
            result = callback(*args, **kwargs)
        except Exception as e:
            self.on_error(e, command)
            return
        kwargs.pop('source')

        if result is None:
            self.logger.debug(' No result from callback on command: %s', command)
        else:
            service = self.messaging._service_name
            self._handle_result(command, source, result, service=service, *args, **kwargs)


    def on_next(self, item: Request) -> None:
        command = item.command
        args = item.args
        kwargs = item.kwargs
        source = item.source
        self.logger.info(' Request recieved, %s %s %s %s',
                         command, source, args, kwargs)

        if not kwargs.get('result'):
            self._handle_command(command, source, *args, **kwargs)
        else:
            # TODO: Verify that this makes sense
            # NOTE: Stripping the first address on here as it should be the bot address
            source = source[1:]
            self._handle_result(command, source, kwargs.pop('result'), *args, **kwargs)

    def on_error(self, error: Exception, command, *args, **kwargs):
        print(_sys.exc_info())
        self.logger.exception(' on_next error for command {}'.format(command))

    def on_completed(self, *args, **kwargs):
        self.logger.info(' command observer completed!')

    @vexcommand(alias=['quit', 'exit'])
    def do_kill_bot(self, *args, **kwargs):
        """
        Kills the instance of vexbot
        """
        self.logger.warn(' Exiting bot!')
        _sys.exit()
