import logging
import pickle

import zmq
import zmq.devices

from vexbot import _get_default_port_config
from vexbot.scheduler import Scheduler
from vexbot.util.socket_factory import SocketFactory as _SocketFactory
from vexbot.util.messaging import get_addresses as _get_addresses
from vexbot.adapters.shell._lru_cache import _LRUCache

from vexmessage import create_vex_message, decode_vex_message, Request


class Messaging:
    """
    Current class responsabilities:
        configuration
        decode
    """

    # TODO: add an `update_messaging` command
    def __init__(self, botname: str='Vexbot', **kwargs):
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
        # Defaults. Can be overriden by the use of `kwargs`
        configuration = _get_default_port_config()
        # override the default with the `kwargs`
        configuration.update(kwargs)

        # Store the addresses of publish, subscription, and heartbeat sockets
        self.configuration = configuration
        self._service_name = botname

        self.subscription_socket = None
        self.publish_socket = None
        self.command_socket = None
        self.control_socket = None
        self.request_socket = None
        self.scheduler = Scheduler(self)

        # The poller polls each socket
        self._logger = logging.getLogger(__name__)

        # Socket factory keeps the zmq context, default ip_address and
        # protocol for socket creation.
        self._socket_factory = _SocketFactory(self.configuration['ip_address'],
                                              self.configuration['protocol'],
                                              logger=self._logger)

        self._address_map = _LRUCache(100)

    def _get_sockets(self) -> tuple:
        sockets = (self.command_socket,
                   self.control_socket,
                   self.publish_socket,
                   self.request_socket,
                   self.subscription_socket)

        return sockets

    def _close_sockets(self):
        sockets = self._get_sockets()
        for socket in sockets:
            if socket is not None:
                socket.close()

    def start(self):
        """
        starts/instantiates the messaging
        """
        self._close_sockets()

        create_n_conn = self._socket_factory.create_n_connect
        to_address = self._socket_factory.to_address

        control_address = to_address(self.configuration['control_port'])

        # NOTE: These sockets will exit the program to exit if there's an issue
        self.control_socket = create_n_conn(zmq.ROUTER,
                                            control_address,
                                            on_error='exit',
                                            bind=True,
                                            socket_name='control socket')

        pub_addrs = to_address(self.configuration['chatter_publish_port'])
        # publish socket is an XSUB socket
        self.publish_socket = create_n_conn(zmq.XSUB,
                                            pub_addrs,
                                            bind=True,
                                            on_error='exit',
                                            socket_name='publish socket')

        # NOTE: these sockets will only log an error if there's an issue
        command_address = to_address(self.configuration['command_port'])
        self.command_socket = create_n_conn(zmq.ROUTER,
                                            command_address,
                                            bind=True)

        request_address = to_address(self.configuration['request_port'])
        self.request_socket = create_n_conn(zmq.DEALER,
                                            request_address,
                                            bind=True,
                                            socket_name='request socket')

        iter_ = self._socket_factory.iterate_multiple_addresses
        sub_addresses = iter_(self.configuration['chatter_subscription_port'])
        # TODO: verify that this shouldn't be like a connect as the socket
        # factory defaults to bind subscription socket is a XPUB socket
        multiple_create = self._socket_factory.multiple_create_n_connect

        name = 'subscription socket'
        self.subscription_socket = multiple_create(zmq.XPUB,
                                                   sub_addresses,
                                                   bind=True,
                                                   socket_name=name)

        self.scheduler.setup()
        self.scheduler.run()

    def send_heartbeat(self, target: str=''):
        frame = self._create_frame('PING', target)
        self.scheduler.add_callback(self.publish_socket.send_multipart, frame)

    def send_chatter(self, target: str='', from_='', *args, **chatter: dict):
        if from_ == '':
            from_ = self._service_name

        frame = create_vex_message(target, self._service_name, 'MSG', **chatter)
        self.scheduler.add_callback(self.subscription_socket.send_multipart,
                                    frame) 

    def send_command(self, command: str, target: str='', *args, **kwargs):
        target = target.encode('ascii')
        command = command.encode('ascii')
        args = pickle.dumps(args)
        kwargs = pickle.dumps(kwargs)
        frame = (target, command, args, kwargs)
        self.command_socket.send_multipart(frame)

    def _get_address_from_source(self, source: str) -> list:
        """
        get the zmq address from the source
        to be used for sending requests to the adapters
        """
        raise NotImplemented()

    def send_request(self, target: str, *args, **kwargs):
        """
        address must a list instance. Or a string which will be transformed into a address
        """
        # TODO: Log error here if not found?
        address = self._get_address_from_source(target)
        if address is None:
            return

        args = pickle.dumps(args)
        kwargs = pickle.dumps(kwargs)

        # TODO: test that this works
        # FIXME: pop out command?
        frame = (*address, b'', b'MSG', args, kwargs)
        self.command_socket.send_multipart(frame)

    def send_control_response(self, source: list, command: str, *args, **kwargs):
        """
        Used in bot observer `on_next` method
        """
        args = pickle.dumps(args)
        kwargs = pickle.dumps(kwargs)
        frame = (*source, b'', command.encode('ascii'), args, kwargs)
        self.scheduler.add_callback(self.command_socket.send_multipart, frame)

    def _get_message_helper(self, socket):
        try:
            msg = socket.recv_multipart(zmq.NOBLOCK)
            try:
                msg = decode_vex_message(msg)
            except Exception as e:
                # FIXME: log error
                pass
        except zmq.error.Again:
            pass

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
        # the command name is the first string in message
        command = message.pop(0).decode('ascii')

        # Respond to PING commands
        if command == 'PING':
            addresses.append(b'PONG')
            self.command_socket.send_multipart(addresses)
            return
        # NOTE: Message format is [command, args, kwargs]
        args = message.pop(0)
        # FIXME: wrap in try/catch and handle gracefully
        # NOTE: pickle is NOT safe
        args = pickle.loads(args)
        # need to see if we have kwargs, so we'll try and pop them off
        try:
            kwargs = message.pop(0)
        except IndexError:
            kwargs = {}
        else:
            # FIXME: wrap in try/catch and handle gracefully
            # NOTE: pickle is NOT safe
            kwargs = pickle.loads(kwargs)
        # TODO: use better names, request? command
        request = Request(command, addresses)
        request.args = args
        request.kwargs = kwargs
        return request
