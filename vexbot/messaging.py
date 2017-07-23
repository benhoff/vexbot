import sys
import logging

import zmq
import zmq.devices

from vexbot import _get_default_port_config

from vexmessage import create_vex_message, decode_vex_message


class Messaging:
    """
    Current class responsabilities:
        configuration
        socket initialization
        decode
        yield
        control
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

        self._service_name = botname
        self.protocol = configuration['protocol']
        self.ip_address = configuration['ip_address']

        # Store the addresses of publish, subscription, and heartbeat sockets
        self.configuration = configuration 
        self.subscription_socket = None
        self.publish_socket = None
        self.command_socket = None
        self.control_socket = None
        self.request_socket = None

        # The poller polls each socket
        self._poller = zmq.Poller()
        self.running = False
        self._logger = logging.getLogger(__name__)

    def start(self, zmq_context: 'zmq.Context'=None):
        """
        starts/instantiates the messaging
        """
        context = zmq_context or zmq.Context()

        # command and control sockets
        self.command_socket = context.socket(zmq.ROUTER)
        self.control_socket = context.socket(zmq.ROUTER)
        self.request_socket = context.socket(zmq.DEALER)

        # command address
        command_address = self.configuration['command_port']
        command_address = self._address_helper(command_address)
        # bind command socket to it's address
        try:
            self.command_socket.bind(command_address)
        except zmq.error.ZMQError:
            self._handle_bind_error_by_log(command_address, 'command')

        # control socket address
        control_address = self.configuration['control_port']
        control_address = self._address_helper(control_address)

        # bind control socket to it's address
        try:
            self.control_socket.bind(control_address)
        except zmq.error.ZMQError:
            self._handle_bind_error_by_exit(control_address, 'control')

        request_address = self.configuration['request_port']
        request_address = self._address_helper(request_address)

        try:
            # TODO: verify that you can do bind a dealer
            self.request_socket.bind(request_address)
        except zmq.error.ZMQError:
            self._handle_bind_error_by_log(request_address, 'request')

        self._poller.register(self.command_socket, zmq.POLLIN)
        self._poller.register(self.control_socket, zmq.POLLIN)
        # TODO: verify that dealer sockets are `zmq.POLLOUT` 
        self._poller.register(self.request_socket, zmq.POLLIN)

        # subscription socket is a XPUB socket
        self.subscription_socket = context.socket(zmq.XPUB)
        # IN type for the poll registration
        self._poller.register(self.subscription_socket, zmq.POLLIN)

        # get all addresses
        addresses = self.configuration['chatter_subscription_port']
        # validate the addresses real quick
        if isinstance(addresses, str):
            # TODO: verify this works.
            addresses = tuple(addresses,)

        # Can subscribe to multiple addresses
        for addr in addresses:
            # NOTE: handle case of a different IP address being passed in
            # TODO: make this much more robust
            if isinstance(addr, int):
                ip_address = self._address_helper(addr) 
            else:
                ip_address = addr

            try:
                self.subscription_socket.bind(ip_address)
            except zmq.error.ZMQError:
                self._handle_bind_error_by_log(ip_address, 'subscription')

        # XSUB socket
        # publish socket is an XSUB socket
        self.publish_socket = context.socket(zmq.XSUB)
        # information comes in for poller purposes
        self._poller.register(self.publish_socket, zmq.POLLIN)

        # grab out the port
        sub_addr = self.configuration['chatter_publish_port']
        # create the address
        sub_addr = self._address_helper(sub_addr)

        # try to bind the pub socket to it's address.
        try:
            self.publish_socket.bind(sub_addr)
        except zmq.error.ZMQError:
            self._handle_bind_error_by_exit(sub_addr, 'publish')

    def send_request(self, target: str, **request: dict):
        pass

    def send_heartbeat(self, target: str=''):
        frame = self._create_frame('PING', target)
        self.publish_socket.send_multipart(frame)

    def send_chatter(self, target: str='', **chatter: dict):
        frame = self._create_frame('CHATTER',
                                   target=target,
                                   contents=chatter) 

        self.subscription_socket.send_multipart(frame)

    # NOTE: not really implemented?
    """
    def send_command(self, target: str, **cmd: dict):
        frame = self._create_frame('CMD', target=target, **cmd)
        self.command_publish_socket.send_multipart(frame)
    """

    def send_response(self, target: str, original: str, **rsp: dict):
        frame = self._create_frame('RSP',
                                   target=target,
                                   original=original,
                                   **rsp)

        self.control_socket.send_multipart(frame)

    def send_response_command(self, target: str, original: str, **rsp: dict):
        frame = self._create_frame('RSP',
                                   target=target,
                                   original=original,
                                   **rsp)

        self.command_socket.send_multipart(frame)

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

    def _address_helper(self, port):
        """
        returns a zmq address
        """
        zmq_address = '{}://{}:{}'
        return zmq_address.format(self.protocol,
                                  self.ip_address,
                                  port)

    def _handle_bind_error_by_log(self, ip_address, socket_type):
        s = 'Address bind attempt fail. Address tried: {}'
        s = s.format(ip_address)
        self._logger.error(s)
        self._logger.error('socket type: {}'.format(socket_type))

    def _handle_bind_error_by_exit(self, ip_address, socket_type):
        s = 'Address bind attempt fail. Address tried: {}'
        s = s.format(ip_address)
        self._logger.error(s)
        self._logger.error('socket type: {}'.format(socket_type))
        sys.exit(1)
