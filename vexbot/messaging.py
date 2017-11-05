import time
import uuid
import json
import logging

import zmq
import zmq.devices
from zmq.eventloop import IOLoop
from zmq.eventloop.ioloop import PeriodicCallback

from rx.subjects import Subject as _Subject

from vexbot import _get_default_port_config
from vexbot.scheduler import Scheduler
from vexbot.util.socket_factory import SocketFactory as _SocketFactory
from vexbot.util.messaging import get_addresses as _get_addresses
from vexbot.util.lru_cache import LRUCache as _LRUCache
from vexbot._logging import MessagingLogger
from vexbot._logging import LoopPubHandler

from vexmessage import create_vex_message, decode_vex_message, Request, Message


class _HeartbeatHelper:
    def __init__(self, messaging, loop):
        self.messaging = messaging
        self.last_message_time = time.time()
        self._heart_beat = PeriodicCallback(self._send_state, 1000, loop)
        name = self.messaging._service_name + '.messaging.heartbeat'
        self.logger = logging.getLogger(name)

    def start(self):
        self.logger.info(' Start Heart Beat')
        self._heart_beat.start()

    def message_recieved(self):
        self.last_message_time = time.time()

    def _send_state(self):
        time_now = time.time()
        delta_time = time_now - self.last_message_time
        if delta_time > 1.5:
            msg = create_vex_message('', self.messaging._service_name, self.messaging.uuid)
            self.messaging.add_callback(self.messaging.subscription_socket.send_multipart, msg)
            self.last_message_time = time_now


class Messaging:
    # TODO: add an `update_messaging` command
    def __init__(self, botname: str='vexbot', **kwargs):
        """
        `kwargs`:
            protocol:   'tcp'
            address: '*'
            chatter_publish_port: 4000
            chatter_subscription_port: [4001,]
            command_port: 4002
            request_port: 4003
            control_port: 4005
        """
        # Defaults. Can be overriden by the use of `kwargs`
        self.config = _get_default_port_config()
        # override the default with the `kwargs`
        self.config = {**self.config, **kwargs}
        self._service_name = botname
        self._logger = logging.getLogger(__name__)
        self._messaging_logger = MessagingLogger(botname)
        self.uuid = str(uuid.uuid1())
        self._logger.info(' uuid: %s', self.uuid)

        self.subscription_socket = None
        self.publish_socket = None
        self.command_socket = None
        self.control_socket = None
        self.request_socket = None
        self.pub_handler = LoopPubHandler(self)

        self.loop = IOLoop()
        self.scheduler = Scheduler()
        self._heartbeat_helper = _HeartbeatHelper(messaging=self, loop=self.loop)


        # Socket factory keeps the zmq context, default address and
        # protocol for socket creation.
        self._socket_factory = _SocketFactory(self.config['address'],
                                              self.config['protocol'],
                                              logger=self._logger,
                                              loop=self.loop)

        # converts from ports to zmq ip addresses
        self._config_convert_to_address_helper()
        self._address_map = _LRUCache(100)

        self.control = _Subject()
        self.command = _Subject()
        self.chatter = _Subject()

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

    def _get_sockets(self) -> tuple:
        sockets = (self.command_socket,
                   self.control_socket,
                   self.publish_socket,
                   self.request_socket,
                   self.subscription_socket)

        return sockets

    def _close_sockets(self):
        sockets = self._get_sockets()
        # self._logger.warn(' closing sockets!')
        for socket in sockets:
            if socket is not None:
                socket.close()

    def start(self):
        self._setup()
        self._heartbeat_helper.start()
        self._logger.info(' start loop')
        return self.loop.start()

    def _setup(self):
        """
        starts/instantiates the messaging
        """
        self._close_sockets()
        create_n_conn = self._socket_factory.create_n_connect

        control_address = self.config['control_port']
        publish_address = self.config['chatter_publish_port']
        request_address = self.config['request_port']
        command_address = self.config['command_port']

        self._messaging_logger.control.info(' Address: %s', control_address)
        # NOTE: These sockets will exit the program to exit if there's an issue
        self.control_socket = create_n_conn(zmq.ROUTER,
                                            control_address,
                                            on_error='exit',
                                            bind=True,
                                            socket_name='control socket')
        self._messaging_logger.publish.info(' Address: %s', publish_address)
        # publish socket is an XSUB socket
        self.publish_socket = create_n_conn(zmq.XSUB,
                                            publish_address,
                                            bind=True,
                                            on_error='exit',
                                            socket_name='publish socket')
        self._messaging_logger.command.info(' Address: %s', command_address)
        # NOTE: these sockets will only log an error if there's an issue
        self.command_socket = create_n_conn(zmq.ROUTER,
                                            command_address,
                                            bind=True)
        self._messaging_logger.request.info(' Address: %s', request_address)
        self.request_socket = create_n_conn(zmq.DEALER,
                                            request_address,
                                            bind=True,
                                            socket_name='request socket')

        iter_ = self._socket_factory.iterate_multiple_addresses
        sub_addresses = iter_(self.config['chatter_subscription_port'])
        # TODO: verify that this shouldn't be like a connect as the socket
        # factory defaults to bind subscription socket is a XPUB socket
        multiple_create = self._socket_factory.multiple_create_n_connect
        name = 'subscription socket'
        self.subscription_socket = multiple_create(zmq.XPUB,
                                                   sub_addresses,
                                                   bind=True,
                                                   socket_name=name)

        info = self._messaging_logger.subscribe.info
        [info(' Address: %s', x) for x in sub_addresses]

        self._setup_scheduler()

    def _setup_scheduler(self):
        self._logger.info(' Registering Sockets')
        # Control Socket
        self.scheduler.register_socket(self.control_socket,
                                       self.loop,
                                       self._control_helper)
        # Command Socket
        self.scheduler.register_socket(self.command_socket,
                                       self.loop,
                                       self._command_helper)
        # Publish Socket
        self.scheduler.register_socket(self.publish_socket,
                                       self.loop,
                                       self._publish_helper)
        # Subscribe Socket
        self.scheduler.register_socket(self.subscription_socket,
                                       self.loop,
                                       self._subscribe_helper)
        # Request Socket
        self.scheduler.register_socket(self.request_socket,
                                       self.loop,
                                       self._request_helper)

    def send_chatter(self, target: str='', from_='', *args, **chatter: dict):
        if from_ == '':
            from_ = self._service_name

        self._messaging_logger.publish.info(' send_chatter to: %s %s',
                                            target,
                                            chatter)

        frame = create_vex_message(target, self._service_name, self.uuid, **chatter)
        self.add_callback(self.subscription_socket.send_multipart,
                          frame) 

    def send_log(self, *args, **kwargs):
        frame = create_vex_message('', self._service_name, self.uuid, **kwargs)
        if self.subscription_socket:
            self.add_callback(self.subscription_socket.send_multipart,
                              frame) 

    def send_command(self, command: str, target: str='', *args, **kwargs):
        target = target.encode('utf-8')
        command = command.encode('utf-8')
        args = json.dumps(args).encode('utf8')
        kwargs = json.dumps(kwargs).encode('utf8')
        self._messaging_logger.command.info('send command %s: %s | %s',
                                            command, args, kwargs)
        frame = (target, command, args, kwargs)
        self.add_callback(self.command_socket.send_multipart, frame)

    def _get_address_from_source(self, source: str) -> list:
        """
        get the zmq address from the source
        to be used for sending requests to the adapters
        """
        raise NotImplemented()

    # FIXME: Not implemented
    def send_request(self, target: str, *args, **kwargs):
        """
        address must a list instance. Or a string which will be transformed into a address
        """
        # TODO: Log error here if not found?
        address = self._get_address_from_source(target)
        if address is None:
            return

        args = json.dumps(args).encode('utf8')
        kwargs = json.dumps(kwargs).encode('utf8')

        # TODO: test that this works
        # NOTE: pop out command?
        frame = (*address, b'', b'MSG', args, kwargs)
        self.add_callback(self.command_socket.send_multipart, frame)

    def send_command_response(self, source: list, command: str, *args, **kwargs):
        """
        Used in bot observer `on_next` method
        """
        args = json.dumps(args).encode('utf8')
        kwargs = json.dumps(kwargs).encode('utf8')
        frame = (*source, b'', command.encode('utf8'), args, kwargs)
        self.add_callback(self.command_socket.send_multipart, frame)

    def _create_frame(self, type_, target='', **contents):
        return create_vex_message(target,
                                  self._service_name,
                                  type_,
                                  **contents)

    def handle_raw_command(self, message: list) -> Request:
        addresses = _get_addresses(message)
        # NOTE: there should be a blank string between
        # the address piece and the message content, which is why
        # we add one to get the correct `address_length`
        address_length = len(addresses) + 1
        # remove the address information from the message
        message = message[address_length:]
        self._messaging_logger.command.debug(' addresses: %s', addresses)
        # the command name is the first string in message
        command = message.pop(0).decode('utf8')
        self._messaging_logger.command.debug(' command: %s', command)

        # Respond to PING commands
        if command == 'PING':
            addresses.append(b'PONG')
            self._messaging_logger.command.info(' Send Pong')
            self.add_callback(self.command_socket.send_multipart,
                              addresses)

            return
        # NOTE: Message format is [command, args, kwargs]
        args = message.pop(0)
        try:
            args = json.loads(args.decode('utf8'))
        except Exception:
            self._logger.exception(' could not load command. Is the json dump\'d correctly?')
            args = ()
        self._messaging_logger.command.debug(' args: %s', args)
        # need to see if we have kwargs, so we'll try and pop them off
        try:
            kwargs = message.pop(0)
        except IndexError:
            kwargs = {}
        else:
            try:
                kwargs = json.loads(kwargs.decode('utf8'))
            except Exception:
                err = ' could not load command. Is the json dump\'d correctly?'
                self._messaging_logger.command.exception(err)
                kwargs = {}
        self._messaging_logger.command.debug(' kwargs: %s', kwargs)

        # TODO: use better names, request? command
        request = Request(command, addresses)
        request.args = args
        request.kwargs = kwargs
        return request

    def add_callback(self, callback, *args, **kwargs):
        self.loop.add_callback(callback, *args, **kwargs)

    def _control_helper(self, msg):
        self._messaging_logger.control.info(' msg recieved')
        request = self.handle_raw_command(msg)

        if request is None:
            return

        self.control.on_next(request)

    def _command_helper(self, msg):
        self._messaging_logger.command.info('msg recieved')
        request = self.handle_raw_command(msg)

        if request is None:
            return

        self.command.on_next(request)

    def _publish_helper(self, msg):
        msg = decode_vex_message(msg)
        self.chatter.on_next(msg)
        # FIXME: Awkward way to replace the uuid by creating a new vexmessage
        msg = create_vex_message(msg.target, msg.source, self.uuid, **msg.contents)
        self.loop.add_callback(self.subscription_socket.send_multipart, msg)
        self._heartbeat_helper.message_recieved()

    def _subscribe_helper(self, msg):
        # TODO: log here?
        self.loop.add_callback(self.publish_socket.send_multipart, msg)

    def _request_helper(self, msg):
        self._messaging_logger.request.info(' request recieved: %s', msg)
