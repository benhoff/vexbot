import logging
import pickle

import zmq
import zmq.devices

from vexbot import _get_default_port_config
from vexbot.util.socket_factory import SocketFactory as _SocketFactory
from vexbot.util.messaging import get_addresses as _get_addresses

from vexmessage import create_vex_message, decode_vex_message, Request


class Messaging:
    """
    Current class responsabilities:
        configuration
        decode
        yield
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

        # The poller polls each socket
        self._poller = zmq.Poller()
        self.running = False
        self._logger = logging.getLogger(__name__)

        # Socket factory keeps the zmq context, default ip_address and
        # protocol for socket creation.
        self._socket_factory = _SocketFactory(self.configuration['ip_address'],
                                              self.configuration['protocol'],
                                              logger=self._logger)

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

        # NOTE: These sockets will cause the program to exit if there's an issue
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
        self.command_socket = create_n_conn(zmq.ROUTER, command_address, bind=True)

        request_address = to_address(self.configuration['request_port'])
        self.request_socket = create_n_conn(zmq.DEALER,
                                            request_address,
                                            bind=True,
                                            socket_name='request socket')

        iter_ = self._socket_factory.iterate_multiple_addresses
        sub_addresses = iter_(self.configuration['chatter_subscription_port'])
        # TODO: verify that this shouldn't be like a connect as the socket factory defaults to bind
        # subscription socket is a XPUB socket
        multiple_create = self._socket_factory.multiple_create_n_connect

        self.subscription_socket = multiple_create(zmq.XPUB,
                                                   sub_addresses,
                                                   bind=True,
                                                   socket_name='subscription socket')

        self._poller.register(self.command_socket, zmq.POLLIN)
        self._poller.register(self.control_socket, zmq.POLLIN)
        # TODO: verify that dealer sockets are `zmq.POLLOUT` 
        self._poller.register(self.request_socket, zmq.POLLIN)
        # IN type for the poll registration
        self._poller.register(self.subscription_socket, zmq.POLLIN)
        # information comes in for poller purposes
        self._poller.register(self.publish_socket, zmq.POLLIN)

    def send_heartbeat(self, target: str=''):
        frame = self._create_frame('PING', target)
        self.publish_socket.send_multipart(frame)

    def send_chatter(self, target: str='', **chatter: dict):
        frame = self._create_frame('CHATTER',
                                   target=target,
                                   contents=chatter) 

        self.subscription_socket.send_multipart(frame)

    def send_control_response(self, source: list, result, command=None):
        source .append(b'')
        send = {'result': result, 'command': command}
        source.append(send)
        self.command_socket.send_mutipart(source)

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
        return create_vex_message(target, self._service_name, type_, **contents)


    def handle_raw_command(self, message) -> Request:
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
        # if we don't have kwargs, then we'll alias our args and pass an
        # empty list in for our args instead.
        except IndexError:
            kwargs = args
            args = []
        else:
            # FIXME: wrap in try/catch and handle gracefully
            # NOTE: pickle is NOT safe
            kwargs = pickle.loads(kwargs)
        
        # TODO: use better names, request? command?
        request = Request(command, addresses, args=args, kwargs=kwargs)
        return request
