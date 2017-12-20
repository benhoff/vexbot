import sys as _sys
import shelve
import logging
import inspect as _inspect
import typing
import importlib
from os import path

from tblib import Traceback

from vexmessage import Request
from vexbot.observer import Observer
from vexbot.messaging import Messaging
from vexbot.intents import intent
from vexbot.command import command
from vexbot.extensions import help as vexhelp
from vexbot.extensions import (develop,
                               hidden,
                               intents,
                               log,
                               subprocess,
                               admin,
                               dynamic_loading)

from vexbot.util.get_cache_filepath import get_cache 
from vexbot.util.create_cache_filepath import create_cache_directory


class CommandObserver(Observer):
    extensions = (develop.get_code,
                  develop.get_members,
                  admin.get_commands,
                  admin.get_disabled,
                  vexhelp.help,
                  hidden.hidden,
                  intents.get_intent,
                  intents.get_intents,
                  admin.disable,
                  admin.enable,
                  dynamic_loading.add_extension,
                  dynamic_loading.get_extensions,
                  dynamic_loading.remove_extensions)

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
        filepath = get_cache(__name__ + '.pickle')
        # FIXME: This will fail if there isn't a dir `~/.cachce/vexbot`
        self._config = shelve.open(filepath, writeback=True)

        if self._config.get('extensions') is None:
            self._config['extensions'] = {}
        if self._config.get('disabled') is None:
            self._config['disabled'] = {}


        self._commands = self._get_commands()
        self._disabled = {}
        self._intents = self._get_intents()
        for value in list(self._config['extensions'].values()):
            self.add_extension(**value)
        self.logger = logging.getLogger(self.messaging._service_name + '.observers.command')

        self._root_logger = logging.getLogger()
        self._root_logger.setLevel(logging.DEBUG)
        logging.basicConfig()
        # self._root_logger.addHandler(self.messaging.pub_handler)

    def _get_intents(self) -> dict:
        result = {}
        # FIXME: define a `None` callback
        # result[None] = self.do_commands
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
            elif getattr(method, 'command', False):
                result[name] = method
            else:
                continue

            if getattr(method,  'alias', False):
                for alias in method.alias:
                    result[alias] = method
        return result

    def do_get_intents(self, *args, **kwargs):
        return self.bot.intents.get_intent_names()

    def do_get_intent(self, *args, **kwargs):
        return self.bot.intents.get_intent_names(*args, **kwargs)

    @command(alias=['MSG',], roles=['admin',])
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

    @command(roles=['admin',])
    def do_NLP(self, *args, **kwargs):
        # FIXME: Do entity extraction here
        intent, confidence, entities = self.language.get_intent(*args, **kwargs)
        self.logger.debug('intent from do_NLP: %s', intent)

        # FIXME: `None` returns `do_command`
        try:
            callback = self._intents[intent]
        except NameError:
            self.logger.debug('intent not found! intent: %s', intent)
            # TODO: send intent back to source
            return

        # FIXME:Pass entites in as kwargs?
        result = callback(*args, entities=entities, **kwargs)
        return result

    @command(roles=['admin',])
    def do_TRAIN_INTENT(self, *args, **kwargs):
        self.logger.debug('starting training!')
        intents = self.bot.intents.get_intents()
        for k, v in intents.items():
            intents[k] = v()
        # self.logger.debug('intents: %s', intents)
        self.language.train_classifier(intents)
        self.logger.debug('training finished')

    @command(roles=['admin',])
    def do_IDENT(self, service_name: str, source: list, *args, **kwargs) -> None:
        """
        Perform identification of a service to a binary representation.

        Args:
            service_name: human readable name for service
            source: zmq representation for the socket source
        """
        self.logger.info(' IDENT %s as %s', service_name, source)
        self.messaging._address_map[service_name] = source

    @command(roles=['admin',])
    def do_AUTH_FOR_SUBSCRIPTION_SOCKET(self):
        self.messaging.subscription_socket.close()
        self.messaging._setup_subscription_socket(True)

    @command(roles=['admin',])
    def do_NO_AUTH_FOR_SUBSCRIPTION_SOCKET(self):
        self.messaging.subscription_socket.close()
        self.messaging._setup_subscription_socket(False)

    @command(roles=['admin',])
    @intent(name='get_services')
    def do_services(self, *args, **kwargs) -> tuple:
        return tuple(self.messaging._address_map.keys())

    @command(alias=['get_last_error',], roles=['admin'])
    @intent(name='get_last_error')
    def do_show_last_error(self, *args, **kwargs):
        exc_info = _sys.exc_info()
        if exc_info[2] is None:
            return 'No problems here boss!'
        self.logger.debug('exc_info: %s', exc_info)
        return Traceback(exc_info[2]).to_dict()

    def _handle_result(self,
                       command: str,
                       source: list,
                       result,
                       *args,
                       **kwargs) -> None:

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
            self._handle_result(command,
                                source,
                                kwargs.pop('result'),
                                *args,
                                **kwargs)

    def on_error(self, error: Exception, command, *args, **kwargs):
        self.logger.warn('on_error called for %s %s %s', command, args, kwargs)
        self.logger.warn('on_error called %s:%s', error.__class__.__name__, error.args)
        self.logger.exception(' on_next error for command {}'.format(command))

    def on_completed(self, *args, **kwargs):
        self.logger.info(' command observer completed!')

    @command(alias=['quit', 'exit'], roles=['admin',])
    @intent(name='exit')
    def do_kill_bot(self, *args, **kwargs):
        """
        Kills the instance of vexbot
        """
        self.logger.warn(' Exiting bot!')
        _sys.exit()
