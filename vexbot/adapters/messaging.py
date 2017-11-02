import uuid
import time
import logging
import json 

import zmq
from zmq.eventloop import IOLoop
from zmq.eventloop.ioloop import PeriodicCallback

from rx.subjects import Subject as _Subject

from vexbot import _get_default_adapter_config
from vexbot._logging import MessagingLogger
from vexbot.util.socket_factory import SocketFactory as _SocketFactory

from vexmessage import create_vex_message, decode_vex_message, Request

from vexbot.util.messaging import get_addresses as _get_addresses
from vexbot.scheduler import Scheduler


class _HeartbeatReciever:
    def __init__(self, messaging, loop, identity_callback=None):
        self.messaging = messaging
        self._heart_beat_check = PeriodicCallback(self._get_state, 1000, loop)
        self.last_message = None
        self._last_bot_uuid = None
        self._last_message_time = time.time()

        name = self.messaging._service_name
        name = name + '.messaging.heartbeat'

        self.logger = logging.getLogger(name)
        self.identity_callback = identity_callback

    def start(self):
        self.logger.info(' Start Heart Beat')
        self._heart_beat_check.start()

    def message_recieved(self, message):
        self._last_message_time = time.time()
        self.last_message = message

    def _get_state(self):
        if self.last_message is None:
            return

        uuid = self.last_message.uuid
        if uuid != self._last_bot_uuid:
            self.logger.info(' UUID message mismatch')
            self.logger.debug(' Old UUID: %s | New UUID: %s',
                              self._last_bot_uuid,
                              uuid)

            self.send_identity()
            self._last_bot_uuid = uuid

    def send_identity(self):
        identify_frame = (b'', 
                          b'IDENT',
                          json.dumps([]).encode('utf8'),
                          json.dumps({'service_name': self.messaging._service_name}).encode('utf8'))

        self.logger.info(' Service Identity sent: %s', self.messaging._service_name)

        if self.messaging._run_control_loop:
            self.messaging.add_callback(self.messaging.command_socket.send_multipart, identify_frame)
        else:
            self.messaging.command_socket.send_multipart(identify_frame)

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
        `socket_configuration`:
            protocol:   'tcp'
            address: '*'
            chatter_publish_port: 4000
            chatter_subscription_port: [4001,]
            command_port: 4002
            request_port: 4003
            control_port: 4005
        """
        self._run_control_loop = run_control_loop
        self.scheduler = Scheduler()
        # Get the default port configurations
        self.config = _get_default_adapter_config()
        # update the default port configurations with the kwargs
        if socket_configuration is not None:
            self.config.update(socket_configuration)

        self.publish_socket = None
        self.subscription_socket = None
        self.command_socket = None
        self.control_socket = None
        self.request_socket = None

        # store the service name and the configuration
        self._service_name = service_name
        self._uuid = str(uuid.uuid1())

        self._socket_filter = socket_filter
        self._logger = logging.getLogger(self._service_name + '.messaging')
        self.loop = IOLoop()

        socket = {'address': self.config['address'],
                  'protocol': self.config['protocol'],
                  'logger': self._logger}

        if run_control_loop:
            socket['loop'] = self.loop

        self._socket_factory = _SocketFactory(**socket)
        # converts the config from ports to zmq ip addresses
        self._config_convert_to_address_helper()

        self._heartbeat_reciever = _HeartbeatReciever(self, self.loop)
        self.chatter = _Subject()
        self.command = _Subject()
        self.request = _Subject()

        self._messaging_logger = MessagingLogger(service_name)

    def _config_convert_to_address_helper(self):
        """
        converts the config from ports to zmq ip addresses
        """
        to_address = self._socket_factory.to_address
        for k, v in self.config.items():
            if k == 'chatter_subscription_port':
                continue
            if k.endswith('port'):
                self.config[k] = to_address(v)

    def add_callback(self, callback, *args, **kwargs):
        self.loop.add_callback(callback, *args, **kwargs)

    def start(self):
        self._setup()

        if self._run_control_loop:
            self._heartbeat_reciever.start()
            self._logger.info(' Start Loop')
            return self.loop.start()
        else:
            self._logger.debug(' run_control_loop == False')

    def _setup(self):
        self._logger.info(' Setup Sockets')
        create_n_conn = self._socket_factory.create_n_connect
        command_address = self.config['command_port']
        control_address = self.config['control_port']
        request_address = self.config['request_port']
        publish_address = self.config['chatter_publish_port']

        # Instantiate all the sockets
        self.command_socket = create_n_conn(zmq.DEALER,
                                            command_address,
                                            socket_name='command socket')
        self._messaging_logger.command.info(' Address: %s', command_address)

        self.control_socket = create_n_conn(zmq.DEALER,
                                            control_address,
                                            socket_name='control socket')
        self._messaging_logger.control.info(' Address: %s', control_address)

        self.request_socket = create_n_conn(zmq.ROUTER,
                                            request_address,
                                            socket_name='request socket')
        self._messaging_logger.request.info(' Address: %s', request_address)

        self.publish_socket = create_n_conn(zmq.PUB,
                                            publish_address,
                                            socket_name='publish socket')
        self._messaging_logger.publish.info(' Address: %s', publish_address)

        iter_ = self._socket_factory.iterate_multiple_addresses
        subscription_address = iter_(self.config['chatter_subscription_port'])
        multiple_conn = self._socket_factory.multiple_create_n_connect
        self.subscription_socket = multiple_conn(zmq.SUB,
                                                 subscription_address,
                                                 socket_name='subscription socket')

        info = self._messaging_logger.subscribe.info
        [info(' Address: %s', x) for x in subscription_address]

        self.set_socket_filter(self._socket_filter)
        if self._run_control_loop:
            self._setup_scheduler()

    def add_callback(self, callback, *args, **kwargs):
        self.loop.add_callback(callback, *args, **kwargs)

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
            self.subscription_socket.setsockopt_string(zmq.SUBSCRIBE, filter_)
            self._messaging_logger.subscribe.info(' Socket Filter: %s',
                                                  filter_)

    def send_chatter(self, target: str='', **msg):
        self._messaging_logger.publish.info(' send_chatter to: %s %s',
                                            target,
                                            msg)

        frame = create_vex_message(target, self._service_name, self._uuid, **msg)
        self._messaging_logger.publish.debug(' Send chatter run_control loop: %s',
                                             self._run_control_loop)

        if self._run_control_loop:
            self.add_callback(self.publish_socket.send_multipart, frame)
        else:
            self.publish_socket.send_multipart(frame)

    def send_log(self, *args, **kwargs):
        frame = create_vex_message('', self._service_name, self._uuid, **kwargs)
        if self._run_control_loop:
            self.add_callback(self.publish_socket.send_multipart,
                              frame) 
        else:
            self.publish_socket.send_multipart(frame)

    def send_command(self, command: str, *args, **kwargs):
        """
        For request bot to perform some action
        """
        self._messaging_logger.command.info('send command %s: %s | %s',
                                            command, args, kwargs)

        command = command.encode('utf8')
        # target = target.encode('ascii')
        args = json.dumps(args).encode('utf8')
        kwargs = json.dumps(kwargs).encode('utf8')
        frame = (b'', command, args, kwargs)
        self._messaging_logger.command.debug(' send command run_control_loop: %s',
                                             self._run_control_loop)

        if self._run_control_loop:
            self.add_callback(self.command_socket.send_multipart, frame)
        else:
            self.command_socket.send_multipart(frame)

    def send_control(self, control, **kwargs):
        """
        Time critical commands
        """
        # FIXME
        # frame = create_vex_message()
        raise NotImplemented()
        self.command_socket.send_multipart(frame)

    def send_response(self, status, target='', **kwargs):
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

    def send_command_response(self, source: list, command: str, *args, **kwargs):
        """
        Used in bot observer `on_next` method
        """
        args = json.dumps(args).encode('utf8')
        kwargs = json.dumps(kwargs).encode('utf8')
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
        except zmq.error.ZMQError:
            pass

        self._address[socket_name] = None

    def _is_pong(self, pong: str):
        if pong == 'PONG':
            self._messaging_logger.command.info('Pong response')
            return True

    def handle_raw_command(self, message) -> Request:
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

        self._messaging_logger.command.debug(' first index in message: %s', first_char)
        # command.
        command = message.pop(0).decode('utf8')
        self._messaging_logger.command.debug(' command: %s', command)

        # NOTE: Message format is [command, args, kwargs]
        args = message.pop(0)
        self._messaging_logger.command.debug('args: %s', args)
        try:
            args = json.loads(args.decode('utf8'))
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
                kwargs = json.loads(kwargs.decode('utf8'))
            except EOFError:
                kwargs = {}
        self._messaging_logger.command.debug(' kwargs: %s', kwargs) 
        # TODO: use better names, request? command?
        # NOTE: this might be different since it's on the other side of the command
        request = Request(command, addresses)
        request.args = args
        request.kwargs = kwargs
        return request

    def _control_helper(self, msg):
        self._messaging_logger.control.info(' recieved message')
        request = self.handle_raw_command(msg)

        if request is None:
            return

        self.control.on_next(request)

    def _command_helper(self, msg):
        self._messaging_logger.command.info(' recieved message')
        request = self.handle_raw_command(msg)

        if request is None:
            return

        self.command.on_next(request)

    def _subscribe_helper(self, msg):
        # TODO: error log? sometimes it's just a subscription notice
        if len(msg) == 1:
            self._messaging_logger.subscribe.debug(' Len message == 1: %s', msg)
            return

        msg = decode_vex_message(msg)
        """
        self._messaging_logger.subscribe.info(' msg recieved: %s %s %s %s',
                                              msg.source,
                                              msg.target,
                                              msg.uuid,
                                              msg.contents)
        """

        self._heartbeat_reciever.message_recieved(msg)
        self.chatter.on_next(msg)

    def _request_helper(self, msg):
        print(msg)
