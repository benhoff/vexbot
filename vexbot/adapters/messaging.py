"""
Attributes:
    Messaging: Used for creating Adapter messaging
"""
import asyncio
import uuid as _uuid
import time as _time
import logging as _logging
import json as _json
import threading as _threading
from typing import Callable as _Callable

import zmq as _zmq
from zmq.eventloop import IOLoop as _IOLoop
from zmq.eventloop.ioloop import PeriodicCallback as _PeriodicCallback

from rx.subjects import Subject as _Subject

from vexbot import _get_default_adapter_config
from vexbot._logging import MessagingLogger as _MessagingLogger
from vexbot.util.socket_factory import SocketFactory as _SocketFactory

from vexmessage import create_vex_message as _create_vex_msg
from vexmessage import decode_vex_message as _decode_vex_msg
from vexmessage import Request as _Request
# NOTE: used only for Typing purposes
from vexmessage import Message as _Message

from vexbot.util.messaging import get_addresses as _get_addresses
from vexbot.scheduler import Scheduler as _Scheduler


# TODO: Change this class to be a `UUIDChecker` or something similar
class _HeartbeatReciever:
    """
    Checks for Robot UUID's in Messages to determine when to send an IDENT
    request.

    Counts a message, or anything coming across the chatter socket as proof of
    life. Call the `start` method to activate, and use the `message_recieved`
    method with each incoming message

    Stores UUID's to represent the latest bot.
    NOTE: Does not support multiple bots, will trigger the `identity_callback`
    repeatedly if there are multiple bots sending messages with different UUIDs
    """
    def __init__(self,
                 # Messaging type defined below
                 messaging,
                 loop: _IOLoop,
                 identity_callback: _Callable=None):

        self.messaging = messaging
        # self._heart_beat_check = _PeriodicCallback(self._get_state, 1000, loop)
        self._heart_beat_check = _PeriodicCallback(self._get_state, 1000)
        self._last_bot_uuid = None
        self.last_message = None
        self._last_message_time = _time.time()

        # logging
        name = self.messaging._service_name
        name = name + '.messaging.heartbeat'
        self.logger = _logging.getLogger(name)

        self.identity_callback = identity_callback

    def start(self):
        """
        Used to start the UUID checking. Non-blocking
        """
        self._heart_beat_check.start()
        self.logger.info(' Started UUID Checking')

    def message_recieved(self, message: _Message):
        """
        """
        self._last_message_time = _time.time()
        self.last_message = message

    def _get_state(self) -> None:
        """
        Internal method that accomplishes checking to make sure that the UUID
        has not changed
        """
        # Don't need to go any further if we don't have a message
        if self.last_message is None:
            return

        # get the latest message UUID
        uuid = self.last_message.uuid
        # Check it against the stored UUID
        if uuid != self._last_bot_uuid:
            self.logger.info(' UUID message mismatch')
            self.logger.debug(' Old UUID: %s | New UUID: %s',
                              self._last_bot_uuid,
                              uuid)

            self.send_identity()
            # Store the latest message UUID now that we've sent an IDENT
            self._last_bot_uuid = uuid

    def send_identity(self):
        """
        Send the identity of the service.
        """
        service_name = {'service_name': self.messaging._service_name}
        service_name = _json.dumps(service_name).encode('utf8')

        identify_frame = (b'',
                          b'IDENT',
                          _json.dumps([]).encode('utf8'),
                          service_name)

        # NOTE: Have to do this manually since we built the frame
        if self.messaging._run_control_loop:
            # pep8 alias
            send = self.messaging.command_socket.send_multipart
            self.messaging.add_callback(send, identify_frame)
        else:
            self.messaging.command_socket.send_multipart(identify_frame)

        self.logger.info(' Service Identity sent: %s',
                         self.messaging._service_name)

        if self.identity_callback:
            self.identity_callback()


class Messaging:
    def __init__(self,
                 service_name: str,
                 socket_filter: str='',
                 run_control_loop: bool=False,
                 socket_configuration: dict=None,
                 **kwargs):
        """
        Adapter Messaging Helper. In the future this class will likely be
        broken into two concerete implementations. In the meantime, do _NOT_
        use the sockets methods individually. If the class is running a
        control loop this will throw an error. Use the `add_callback` method
        if you must to access the socket methods.

        If you do not use the internal control loop, you will have to recv
        each method individually, and call the `on_next` method for the
        appropriate subject

        Args:
            service_name (str): The name of the service that this messaging
                will provide. If multiple instances are to be launched, need
                generate a unique service name everytime or it will cause
                errors
            socket_filter (str): An optional filter to put on the chatter
                socket. Recommend leaving as is unless you are publishing
                chatter messages with targets.
            run_control_loop (bool): If `True`, this class will run all of
                it's code asyncrously using an `IOLoop`. If `False`, all called
                commands will be blocking in a sense. Recommend setting this
                to `True` unless you are integrating another control loop in
                place of `IOLoop`.
            socket_configuration (:obj:`dict`, optional): The zmq socket
                configuration. Defaults to a locally run assistant, show below
                {
                    'protocol':   'tcp'
                    'address': '127.0.0.1'
                    'chatter_publish_port': 4000
                    'chatter_subscription_port': [4001,]
                    'command_port': 4002
                    'request_port': 4003
                    'control_port': 4005
                }
            **kwargs: Currently unused

        Attributes:
            chatter (rx.Subject): Use the `subscribe` method on this to get
                access to all imcoming messages, including heartbeats.
            command (rx.Subject): Use the `subscribe` method on this to get
                access to all incoming commands coming from the robot.
            request (rx.Subject): Currently unused
            send_chatter (Callable): Send chatter to the robot. Useful for
                chat systems such as IRC/XMPP/Slack, etc.
            send_command (Callable): Send a command to the robot. Be careful
                to authenticate your users as the robot has no authentication.
            send_command_response (Callable): Send a response back to the
                robot in response to a command
            add_callback (Callable): add a callback to the control loop if it
                is being run
            run (Callable): run the internal event loop
        """
        self._run_control_loop = run_control_loop
        # Get the default port configurations
        self.config = _get_default_adapter_config()
        # update the default port configurations with the kwargs
        if socket_configuration is not None:
            self.config.update(socket_configuration)

        # sockets intiialized using `self._setup()`
        self.publish_socket = None
        self.subscription_socket = None
        self.command_socket = None
        self.control_socket = None
        self.request_socket = None

        self.chatter = _Subject()
        self.command = _Subject()
        self.request = _Subject()

        # store the service name and the configuration
        self._service_name = service_name
        # Create a uuid for the service
        self._uuid = str(_uuid.uuid1())

        self._socket_filter = socket_filter
        self._logger = _logging.getLogger(self._service_name + '.messaging')
        socket = {'address': self.config['address'],
                  'protocol': self.config['protocol'],
                  'logger': self._logger}

        # NOTE: Internal control loop. This is instantiated regardless of if
        # it's used. This will likely be split into it's own concrete class
        # at some point.
        self.loop = _IOLoop()

        if run_control_loop:
            socket['loop'] = self.loop

        self._socket_factory = _SocketFactory(**socket)
        # converts the config from ports to zmq ip addresses
        self._config_convert_to_address_helper()

        # Overhead/Implementation attributes
        self._run_thread = None
        self._heartbeat_reciever = _HeartbeatReciever(self, self.loop)
        self.chatter.subscribe(self._heartbeat_reciever.message_recieved)

        self._messaging_logger = _MessagingLogger(service_name)
        # FIXME: push this code/logic into `_SocketFactory`
        self.scheduler = _Scheduler()

    def _config_convert_to_address_helper(self) -> None:
        """
        converts the config from ports to zmq ip addresses
        Operates on `self.config` using `self._socket_factory.to_address`
        """
        to_address = self._socket_factory.to_address
        for k, v in self.config.items():
            if k == 'chatter_subscription_port':
                continue
            if k.endswith('port'):
                self.config[k] = to_address(v)

    def add_callback(self, callback: _Callable, *args, **kwargs) -> None:
        """
        Add a callback to the event loop
        """
        self.loop.add_callback(callback, *args, **kwargs)

    def start(self) -> None:
        """
        Start the internal control loop. Potentially blocking, depending on
        the value of `_run_control_loop` set by the initializer.
        """
        self._setup()

        if self._run_control_loop:
            asyncio.set_event_loop(asyncio.new_event_loop())
            self._heartbeat_reciever.start()
            self._logger.info(' Start Loop')
            return self.loop.start()
        else:
            self._logger.debug(' run_control_loop == False')

    def run(self, blocking: bool=True):
        """
        Run the internal control loop.
        Args:
            blocking (bool): Defaults to `True`. If set to `False`, will
                intialize a thread to run the control loop.
        Raises:
            RuntimeError: If called and not using the internal control loop
                via `self._run_control_loop`, set in the intializer of the
                class
        """
        if not self._run_control_loop:
            err = ("`run` called, but not using the internal control loop. Use"
                   " `start` instead")

            raise RuntimeError(err)

        self._setup()
        self._heartbeat_reciever.start()

        if blocking:
            return self.loop.start()
        else:
            self._run_thread = _threading.Thread(target=self.loop.start,
                                                 daemon=True)

            self._thread.run()

    def _setup(self):
        self._logger.info(' Setup Sockets')
        create_n_conn = self._socket_factory.create_n_connect
        command_address = self.config['command_port']
        control_address = self.config['control_port']
        request_address = self.config['request_port']
        publish_address = self.config['chatter_publish_port']

        # Instantiate all the sockets
        self.command_socket = create_n_conn(_zmq.DEALER,
                                            command_address,
                                            socket_name='command socket')
        self._messaging_logger.command.info(' Address: %s', command_address)

        self.control_socket = create_n_conn(_zmq.DEALER,
                                            control_address,
                                            socket_name='control socket')
        self._messaging_logger.control.info(' Address: %s', control_address)

        self.request_socket = create_n_conn(_zmq.ROUTER,
                                            request_address,
                                            socket_name='request socket')
        self._messaging_logger.request.info(' Address: %s', request_address)

        self.publish_socket = create_n_conn(_zmq.PUB,
                                            publish_address,
                                            socket_name='publish socket')
        self._messaging_logger.publish.info(' Address: %s', publish_address)

        iter_ = self._socket_factory.iterate_multiple_addresses
        subscription_address = iter_(self.config['chatter_subscription_port'])
        multiple_conn = self._socket_factory.multiple_create_n_connect

        # pep8 alias
        s_socket = 'subscription socket'
        self.subscription_socket = multiple_conn(_zmq.SUB,
                                                 subscription_address,
                                                 socket_name=s_socket)

        info = self._messaging_logger.subscribe.info
        [info(' Address: %s', x) for x in subscription_address]

        self.set_socket_filter(self._socket_filter)
        if self._run_control_loop:
            self._setup_scheduler()

    def _setup_scheduler(self):
        self._logger.info(' Registering sockets to the IO Loop.')
        # Control Socket
        self.scheduler.register_socket(self.control_socket,
                                       self.loop,
                                       self._control_helper)
        # Command Socket
        self.scheduler.register_socket(self.command_socket,
                                       self.loop,
                                       self._command_helper)
        # Subscribe Socket
        self.scheduler.register_socket(self.subscription_socket,
                                       self.loop,
                                       self._subscribe_helper)
        # Request Socket
        self.scheduler.register_socket(self.request_socket,
                                       self.loop,
                                       self._request_helper)

    def set_socket_filter(self, filter_):
        self._socket_filter = filter_

        if self.subscription_socket:
            self.subscription_socket.setsockopt_string(_zmq.SUBSCRIBE, filter_)
            self._messaging_logger.subscribe.info(' Socket Filter: %s',
                                                  filter_)

    def send_chatter(self, target: str='', **msg):
        self._messaging_logger.publish.info(' send_chatter to: %s %s',
                                            target,
                                            msg)

        frame = _create_vex_msg(target,
                                self._service_name,
                                self._uuid,
                                **msg)

        debug = ' Send chatter run_control loop: %s'
        self._messaging_logger.publish.debug(debug, self._run_control_loop)

        if self._run_control_loop:
            self.add_callback(self.publish_socket.send_multipart, frame)
        else:
            self.publish_socket.send_multipart(frame)

    def send_log(self, *args, **kwargs):
        frame = _create_vex_msg('',
                                self._service_name,
                                self._uuid,
                                **kwargs)

        if self._run_control_loop:
            self.add_callback(self.publish_socket.send_multipart,
                              frame)
        else:
            self.publish_socket.send_multipart(frame)

    def send_command(self, command: str, *args, **kwargs):
        """
        For request bot to perform some action
        """
        info = 'send command `%s` to bot. Args: %s | Kwargs: %s'
        self._messaging_logger.command.info(info, command, args, kwargs)

        command = command.encode('utf8')
        # target = target.encode('ascii')
        args = _json.dumps(args).encode('utf8')
        kwargs = _json.dumps(kwargs).encode('utf8')
        frame = (b'', command, args, kwargs)
        debug = ' send command run_control_loop: %s'
        self._messaging_logger.command.debug(debug, self._run_control_loop)

        if self._run_control_loop:
            self.add_callback(self.command_socket.send_multipart, frame)
        else:
            self.command_socket.send_multipart(frame)

    def send_control(self, control, **kwargs):
        """
        Time critical commands
        """
        # FIXME
        raise NotImplemented()
        # frame = create_vex_message()
        # self.command_socket.send_multipart(frame)

    def send_response(self, status, target='', **kwargs):
        """
        NOT IMPLEMENTED
        """

        """
        frame = create_vex_message(target,
                                   self._service_name,
                                   'STATUS',
                                   status=status,
                                   **kwargs)

        self.request_socket.send_multipart(frame)
        """
        raise NotImplemented()

    def send_ping(self, target: str=''):
        self._logger.debug('send ping to %s', target)
        frame = (target.encode('utf8'), b'PING')
        if self._run_control_loop:
            self.add_callback(self.command_socket.send_multipart, frame)
        else:
            self.command_socket.send_multipart(frame)

    def send_command_response(self,
                              source: list,
                              command: str,
                              *args,
                              **kwargs):
        """
        Used in bot observer `on_next` method
        """
        args = _json.dumps(args).encode('utf8')
        kwargs = _json.dumps(kwargs).encode('utf8')
        if isinstance(source, list):
            frame = (*source, b'', command.encode('utf8'), args, kwargs)
        else:
            frame = (b'', command.encode('utf8'), args, kwargs)
        if self._run_control_loop:
            self.add_callback(self.command_socket.send_multipart, frame)
        else:
            self.command_socket.send_multipart(frame)

    def _send_pong(self, addresses: list):
        self._messaging_logger.command.info(' send pong to %s', addresses)
        addresses.append(b'PONG')
        self._messaging_logger.command.debug(' send pong run_control_loop: %s',
                                             self._run_control_loop)

        if self._run_control_loop:
            self.add_callback(self.command_socket.send_multipart,
                              addresses)

        else:
            self.command_socket.send_multipart(addresses)

    def _disconnect_socket(self, socket, socket_name, address=None):
        if address is None:
            address = self._address[socket_name]

        # can have `None` for value
        if not address:
            return
        try:
            socket.disconnect(address)
        except _zmq.error.ZMQError:
            pass

        self._address[socket_name] = None

    def _is_pong(self, pong: str):
        if pong == 'PONG':
            self._messaging_logger.command.info('Pong response')
            return True

    def _handle_raw_command(self, message) -> _Request:
        # blank string
        first_char = message.pop(0)
        is_address = False
        try:
            first_char = first_char.decode('utf-8')
            is_pong = self._is_pong(first_char)
        except UnicodeDecodeError:
            is_pong = False
            is_address = True

        if is_pong:
            return

        if is_address:
            addresses = _get_addresses(message)
            addresses.insert(0, first_char)
            message.pop(0)
        else:
            addresses = None

        debug = ' first index in message: %s'
        self._messaging_logger.command.debug(debug, first_char)
        # command.
        command = message.pop(0).decode('utf8')
        self._messaging_logger.command.debug(' command: %s', command)

        # NOTE: Message format is [command, args, kwargs]
        args = message.pop(0)
        self._messaging_logger.command.debug('args: %s', args)
        try:
            args = _json.loads(args.decode('utf8'))
        except EOFError:
            args = ()
        # need to see if we have kwargs, so we'll try and pop them off
        try:
            kwargs = message.pop(0)
        # if we don't have kwargs, then we'll alias our args and pass an
        # empty list in for our args instead.
        except IndexError:
            pass
        else:
            try:
                kwargs = _json.loads(kwargs.decode('utf8'))
            except EOFError:
                kwargs = {}
        self._messaging_logger.command.debug(' kwargs: %s', kwargs)
        # TODO: use better names, request? command?
        # NOTE: this might be different since it's on the other side of the
        # command
        request = _Request(command, addresses)
        request.args = args
        request.kwargs = kwargs
        return request

    def _control_helper(self, msg):
        # FIXME: Create accessors to get the messages
        # _control_helper -> handle_control_message?
        # What for creating a public API for our non-control loop users.
        self._messaging_logger.control.info(' recieved message')
        request = self._handle_raw_command(msg)

        if request is None:
            return

        self.control.on_next(request)

    def _command_helper(self, msg):
        # FIXME: Create accessors to get the messages
        # _control_helper -> handle_control_message?
        # What for creating a public API for our non-control loop users.
        self._messaging_logger.command.info(' recieved message')
        request = self._handle_raw_command(msg)

        if request is None:
            return

        self.command.on_next(request)

    def _subscribe_helper(self, msg):
        # TODO: error log? sometimes it's just a subscription notice
        if len(msg) == 1:
            debug = ' Len message == 1: %s'
            self._messaging_logger.subscribe.debug(debug, msg)
            return

        msg = _decode_vex_msg(msg)
        """
        self._messaging_logger.subscribe.info(' msg recieved: %s %s %s %s',
                                              msg.source,
                                              msg.target,
                                              msg.uuid,
                                              msg.contents)
        """
        self.chatter.on_next(msg)

    def _request_helper(self, msg):
        """
        NOT IMPLEMENTED
        """
        print(msg)
