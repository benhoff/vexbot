import uuid
import time
import logging
import json 

import zmq
from zmq.eventloop import IOLoop
from zmq.eventloop.ioloop import PeriodicCallback

from rx.subjects import Subject as _Subject

from vexbot import _get_default_port_config
from vexbot.util.socket_factory import SocketFactory as _SocketFactory

from vexmessage import create_vex_message, decode_vex_message, Request

from vexbot.util.messaging import get_addresses as _get_addresses
from vexbot.scheduler import Scheduler


class _HeartbeatReciever:
    def __init__(self, messaging, loop):
        self.messaging = messaging
        self._heart_beat_check = PeriodicCallback(self._get_state, 1000, loop)
        self._last_bot_uuid = None
        self.last_message = None
        self.last_message_time = None
        self._last_message = time.time()

    def start(self):
        self._heart_beat_check.start()

    def message_recieved(self, message):
        self._last_message = time.time()
        self.last_message = message

    def _get_state(self):
        if self.last_message is None:
            return

        uuid = self.last_message.uuid
        if uuid != self._last_bot_uuid:
            self.send_identity()
            self._last_bot_uuid = uuid

    def send_identity(self):
        identify_frame = (b'', 
                          b'IDENT',
                          json.dumps([]).encode('utf8'),
                          json.dumps({'service_name': self.messaging._service_name}).encode('utf8'))

        if self.messaging._run_control_loop:
            self.messaging.add_callback(self.messaging.command_socket.send_multipart, identify_frame)
        else:
            self.messaging.command_socket.send_multipart(identify_frame)


class Messaging:
    def __init__(self,
                 service_name: str,
                 socket_filter: str='',
                 run_control_loop: bool=False,
                 **kwargs):
        """
        `kwargs`:
            protocol:   'tcp'
            ip_address: '127.0.0.1'
            chatter_publish_port: 4000
            chatter_subscription_port: [4001,]
            command_port: 4002
            request_port: 4003
            control_port: 4005
        """
        self._run_control_loop = run_control_loop
        self.scheduler = Scheduler()
        # Get the default port configurations
        self.config = _get_default_port_config()
        # update the default port configurations with the kwargs
        self.config.update(kwargs)

        self.publish_socket = None
        self.subscription_socket = None
        self.command_socket = None
        self.control_socket = None
        self.request_socket = None

        # store the service name and the configuration
        self._service_name = service_name
        self._uuid = str(uuid.uuid1())

        self._socket_filter = socket_filter
        self._logger = logging.getLogger(self._service_name)
        self.loop = IOLoop()

        socket = {'ip_address': self.config['ip_address'],
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
            return self.loop.start()

    def _setup(self):
        create_n_conn = self._socket_factory.create_n_connect

        # Instantiate all the sockets
        self.command_socket = create_n_conn(zmq.DEALER,
                                            self.config['command_port'],
                                            socket_name='command socket')
        self.control_socket = create_n_conn(zmq.DEALER,
                                            self.config['control_port'],
                                            socket_name='control socket')
        self.request_socket = create_n_conn(zmq.ROUTER,
                                            self.config['request_port'],
                                            socket_name='request socket')
        self.publish_socket = create_n_conn(zmq.PUB,
                                            self.config['chatter_publish_port'],
                                            socket_name='publish socket')

        iter_ = self._socket_factory.iterate_multiple_addresses
        subscription_address = iter_(self.config['chatter_subscription_port'])
        multiple_conn = self._socket_factory.multiple_create_n_connect
        self.subscription_socket = multiple_conn(zmq.SUB,
                                                 subscription_address,
                                                 socket_name='subscription socket')

        self.set_socket_filter(self._socket_filter)
        if self._run_control_loop:
            self._setup_scheduler()

    def add_callback(self, callback, *args, **kwargs):
        self.loop.add_callback(callback, *args, **kwargs)

    def _setup_scheduler(self):
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

    def send_chatter(self, target: str='', **msg):
        frame = create_vex_message(target, self._service_name, self._uuid, **msg)
        if self._run_control_loop:
            self.add_callback(self.publish_socket.send_multipart, frame)
        else:
            self.publish_socket.send_multipart(frame)

    def send_command(self, command: str, *args, **kwargs):
        """
        For request bot to perform some action
        """
        command = command.encode('utf8')
        # target = target.encode('ascii')
        args = json.dumps(args).encode('utf8')
        kwargs = json.dumps(kwargs).encode('utf8')
        frame = (b'', command, args, kwargs)
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
        raise RuntimeError('Not implemented')

    def send_ping(self, target: str=''):
        frame = (target.encode('utf8'), b'PING')
        if self._run_control_loop:
            self.add_callback(self.command_socket.send_multipart, frame)
        else:
            self.command_socket.send_multipart(frame)

    def _send_pong(self, addresses: list):
        addresses.append(b'PONG')
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

    def handle_raw_command(self, message) -> Request:
        # blank string
        pong = message.pop(0).decode('utf8')
        # FIXME
        if pong == 'PONG':
            return
        # command? Not sure if we want to do it this way.
        command = message.pop(0).decode('utf8')

        # NOTE: Message format is [command, args, kwargs]
        args = message.pop(0)
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
        
        # TODO: use better names, request? command?
        # NOTE: this might be different since it's on the other side of the command
        request = Request(command, None)
        request.args = args
        request.kwargs = kwargs
        return request

    def _control_helper(self, msg):
        request = self.handle_raw_command(msg)

        if request is None:
            return

        self.control.on_next(request)

    def _command_helper(self, msg):
        request = self.handle_raw_command(msg)

        if request is None:
            return

        self.command.on_next(request)

    def _subscribe_helper(self, msg):
        # TODO: error log? sometimes it's just a subscription notice
        if len(msg) == 1:
            return

        msg = decode_vex_message(msg)
        self._heartbeat_reciever.message_recieved(msg)
        self.chatter.on_next(msg)

    def _request_helper(self, msg):
        print(msg)
