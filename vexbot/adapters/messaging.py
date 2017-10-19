import logging
import pickle

import zmq
from vexbot import _get_default_port_config
from vexbot.util.socket_factory import SocketFactory as _SocketFactory

from vexmessage import create_vex_message, decode_vex_message, Request

from vexbot.util.messaging import get_addresses as _get_addresses
from vexbot.adapters.scheduler import Scheduler


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
        self.scheduler = Scheduler(self)
        # Get the default port configurations
        configuration = _get_default_port_config()
        # update the default port configurations with the kwargs
        configuration.update(kwargs)
        self.publish_socket = None
        self.subscription_socket = None
        self.command_socket = None
        self.control_socket = None
        self.request_socket = None

        self._pong_callback = None
        self.poller = zmq.Poller()

        # store the service name and the configuration
        self._service_name = service_name
        self._configuration = configuration

        self._socket_filter = socket_filter
        self._messaging_started = False
        self._logger = logging.getLogger(self._service_name)

        self._socket_factory = _SocketFactory(configuration['ip_address'],
                                              configuration['protocol'],
                                              logger=self._logger)

    def start(self):
        create_n_conn = self._socket_factory.create_n_connect
        to_address = self._socket_factory.to_address

        # Instantiate all the sockets
        command_address = to_address(self._configuration['command_port'])
        self.command_socket = create_n_conn(zmq.DEALER,
                                            command_address,
                                            socket_name='command socket')

        control_address = to_address(self._configuration['control_port'])
        self.control_socket = create_n_conn(zmq.DEALER,
                                            control_address,
                                            socket_name='control socket')

        request_address = to_address(self._configuration['request_port'])
        self.request_socket = create_n_conn(zmq.ROUTER,
                                            request_address,
                                            socket_name='request socket')

        publish_address = to_address(self._configuration['chatter_publish_port'])
        self.publish_socket = create_n_conn(zmq.PUB,
                                            publish_address,
                                            socket_name='publish socket')

        iter_ = self._socket_factory.iterate_multiple_addresses
        subscription_address = iter_(self._configuration['chatter_subscription_port'])
        multiple_conn = self._socket_factory.multiple_create_n_connect
        self.subscription_socket = multiple_conn(zmq.SUB,
                                                 subscription_address,
                                                 socket_name='subscription socket')

        self.set_socket_filter(self._socket_filter)
        identify_frame = (b'', b'IDENT', pickle.dumps([]), pickle.dumps({'service_name': self._service_name}))

        if self._run_control_loop:
            self.scheduler.setup()
            self.scheduler.add_callback(self.command_socket.send_multipart, identify_frame)
        else:
            self.command_socket.send_multipart(identify_frame)

        self._messaging_started = True

    def set_socket_filter(self, filter_):
        self._socket_filter = filter_

        if self.subscription_socket:
            self.subscription_socket.setsockopt_string(zmq.SUBSCRIBE, filter_)

    def send_chatter(self, target: str='', **msg):
        frame = create_vex_message(target, self._service_name, 'MSG', **msg)
        if self._run_control_loop:
            self.scheduler.add_callback(self.publish_socket.send_multipart, frame)
        else:
            self.publish_socket.send_multipart(frame)

    def send_command(self, command: str, *args, **kwargs):
        """
        For request bot to perform some action
        """
        command = command.encode('ascii')
        # target = target.encode('ascii')
        args = pickle.dumps(args)
        kwargs = pickle.dumps(kwargs)
        frame = (b'', command, args, kwargs)
        if self._run_control_loop:
            self.scheduler.add_callback(self.command_socket.send_multipart, frame)
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
        frame = (target.encode('ascii'), b'PING')
        if self._run_control_loop:
            self.scheduler.add_callback(self.command_socket.send_multipart, frame)
        else:
            self.command_socket.send_multipart(frame)

    def _send_pong(self, addresses: list):
        addresses.append(b'PONG')
        if self._run_control_loop:
            self.scheduler.add_callback(self.command_socket.send_multipart,
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
        pong = message.pop(0).decode('ascii')
        # FIXME
        if pong == 'PONG':
            return
        # command? Not sure if we want to do it this way.
        command = message.pop(0).decode('ascii')

        # NOTE: Message format is [command, args, kwargs]
        args = message.pop(0)
        # FIXME: wrap in try/catch and handle gracefully
        # NOTE: pickle is NOT safe
        try:
            args = pickle.loads(args)
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
            # FIXME: wrap in try/catch and handle gracefully
            # NOTE: pickle is NOT safe
            try:
                kwargs = pickle.loads(kwargs)
            except EOFError:
                kwargs = {}
        
        # TODO: use better names, request? command?
        # NOTE: this might be different since it's on the other side of the command
        request = Request(command, None)
        request.args = args
        request.kwargs = kwargs
        return request
