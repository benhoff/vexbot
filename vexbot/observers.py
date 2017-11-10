import sys as _sys
import logging
import inspect as _inspect
import typing

from rx import Observer

from vexmessage import Request
from vexbot.messaging import Messaging
from vexbot.intents import intent
from vexbot.command import command


class CommandObserver(Observer):
    def __init__(self,
                 bot,
                 messaging: Messaging,
                 subprocess_manager: 'vexbot.subprocess_manager.SubprocessManager',
                 language):

        super().__init__()
        self.bot = bot
        self.messaging = messaging
        self.subprocess_manager = subprocess_manager
        self.language = language
        self._commands = self._get_commands()
        self._intents = self._get_intents()
        self.logger = logging.getLogger(self.messaging._service_name + '.observers.command')

        self._root_logger = logging.getLogger()
        self._root_logger.setLevel(logging.DEBUG)
        logging.basicConfig()
        #self._root_logger.addHandler(self.messaging.pub_handler)

    def _get_intents(self) -> dict:
        result = {}
        # FIXME: define a `None` callback
        result[None] = self.do_commands
        for name, method in _inspect.getmembers(self):
            is_intent = getattr(method, '_vex_intent', False)
            if name.startswith('do_') or is_intent:
                try:
                    name = method._vex_intent_name
                except AttributeError:
                    name = name[3:]
                result[name] = method

        return result

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

    @command(alias=['MSG',])
    def do_REMOTE(self,
                  target: str,
                  remote_command: str,
                  source: list,
                  *args,
                  **kwargs) -> None:
        """
        Send a remote command to a service. Used 

        Args:
            target: The service that the command gets set to
            remote_command: The command to do remotely.
            source: the binary source of the zmq_socket. Packed to send to the
        """
        if target == self.messaging._service_name:
            info = 'target for remote command is the bot itself! Returning the function'
            self.logger.info(info)
            return self._handle_command(remote_command, source, *args, **kwargs)

        try:
            target = self.messaging._address_map[target]
        except KeyError:
            warn = ' Target %s, not found in addresses. Are you sure that %s sent an IDENT message?'
            self.logger.warn(warn, target, target)
            # TODO: raise an error instead of returning?
            # NOTE: Bail here since there's no point in going forward
            return

        self.logger.info(' REMOTE %s, target: %s | %s, %s',
                         remote_command, target, args, kwargs)

        # package the binary together
        source = target + source
        self.messaging.send_command_response(source,
                                             remote_command,
                                             *args, 
                                             **kwargs)

    def do_NLP(self, *args, **kwargs):
        # NOTE: entity feature extraction is already considered in this
        # as part of the classifier
        intent, confidence = self.language.get_intent(*args, **kwargs)
        self.logger.debug('intent from do_NLP: %s', intent)

        try:
            callback = self._intents[intent]
        except NameError:
            self.logger.debug('intent not found! intent: %s', intent)
            # TODO: send intent back to source
            return

        # FIXME
        # entities = self.language.get_entities(*args, **kwargs)

        # FIXME:Pass entites in as kwargs?
        result = callback(*args, **kwargs)
        return result

    def do_TRAIN_INTENT(self, *args, **kwargs):
        self.logger.debug('starting training!')
        intents = self.bot.intents.get_intents()
        for k, v in intents.items():
            intents[k] = v()
        # self.logger.debug('intents: %s', intents)
        self.language.train_classifier(intents)
        self.logger.debug('training finished')

    def do_IDENT(self, service_name: str, source: list, *args, **kwargs) -> None:
        """
        Perform identification of a service to a binary representation.

        Args:
            service_name: human readable name for service
            source: zmq representation for the socket source
        """
        self.logger.info(' IDENT %s as %s', service_name, source)
        self.messaging._address_map[service_name] = source

    @intent(name='get_log')
    @intent(name='set_log')
    def do_log_level(self,
                     level: typing.Union[str, int]=None,
                     *args,
                     **kwargs) -> typing.Union[None, str]:
        """
        Args:
            level:

        Returns:
            The log level if a `level` is passed in
        """
        if level is None:
            return self._root_logger.getEffectiveLevel()
        try:
            value = int(level)
        except ValueError:
            pass

        self._root_logger.setLevel(value)

    @intent(name='get_services')
    def do_services(self, *args, **kwargs) -> tuple:
        return tuple(self.messaging._address_map.keys())

    @intent(name='get_help')
    def do_help(self, *arg, **kwargs) -> str:
        """
        Help helps you figure out what commands do.
        Example usage: !help code
        To see all commands: !commands

        Raises:
            IndexError: if no argument is passed in
        """
        # TODO: return general help if there is a IndexError here
        name = arg[0]
        try:
            callback = self._commands[name]
        except KeyError:
            self._logger.info(' !help not found for: %s', name)
            return self.do_help.__doc__

        return callback.__doc__

    def do_debug(self, *args, **kwargs) -> None:
        self._root_logger.setLevel(logging.DEBUG)
        self.messaging.pub_handler.setLevel(logging.DEBUG)

    @command(alias=['source',])
    @intent(name='get_code')
    def do_code(self, command: str, *args, **kwargs) -> str:
        """
        get the python source code from callback
        Returns:
            str: the source code of the argument

        Raises:
            KeyError: if the `command` is not found in `self._commands`
        """
        # TODO: Throw a better error here
        callback = self._commands[command]
        # TODO: syntax color would be nice
        source = _inspect.getsourcelines(callback)
        # FIXME: formatting sucks
        return "\n" + "".join(source[0])

    def do_warn(self, *args, **kwargs) -> None:
        """
        Sets the log level to `WARN`
        """
        self._root_logger.setLevel(logging.WARN)
        self.messaging.pub_handler.setLevel(logging.WARN)

    def do_info(self, *args, **kwargs) -> None:
        """
        Sets the log level to `INFO`
        """
        self._root_logger.setLevel(logging.INFO)
        self.messaging.pub_handler.setLevel(logging.INFO)

    @intent(name='start_program')
    def do_start(self, name: str, mode: str='replace', *args, **kwargs) -> None:
        """
        Start a program.

        Args:
            name: The name of the serivce. Will often end with `.service` or
                `.target`. If no argument is provided, will default to
                `.service`
            mode:

        Raises:
            GError: if the service is not found
        """
        self.logger.info(' start service %s in mode %s', name, mode)
        self.subprocess_manager.start(name, mode)

    @intent(name='get_commands')
    def do_commands(self, *args, **kwargs) -> tuple:
        commands = tuple(self._commands.keys())
        return commands

    @command(alias=['reboot',])
    @intent(name='restart_program')
    def do_restart(self, name: str, mode: str='replace', *args, **kwargs) -> None:
        self.logger.info(' restart service %s in mode %s', name, mode)
        self.subprocess_manager.restart(name, mode)

    @intent(name='stop_program')
    def do_stop(self, name: str, mode: str='replace', *args, **kwargs) -> None:
        self.logger.info(' stop service %s in mode %s', name, mode)
        self.subprocess_manager.stop(name, mode)

    @intent(name='get_status')
    def do_status(self, name: str) -> str:
        self.logger.info(' get status for %s', name)
        return self.subprocess_manager.status(name)

    def _handle_result(self, command: str, source: list, result, *args, **kwargs) -> None:
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
            self.on_error(e, command, *args, **kwargs)
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
        self.logger.warn('on_error called for %s %s %s', command, args, kwargs)
        self.logger.warn('on_error called %s', error.__class__.__name__)
        self.logger.warn('on_error called %s', error.args)
        self.logger.exception(' on_next error for command {}'.format(command))

    def on_completed(self, *args, **kwargs):
        self.logger.info(' command observer completed!')

    @command(alias=['quit', 'exit'])
    @intent(name='exit')
    def do_kill_bot(self, *args, **kwargs):
        """
        Kills the instance of vexbot
        """
        self.logger.warn(' Exiting bot!')
        _sys.exit()

    @intent(name='help')
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
