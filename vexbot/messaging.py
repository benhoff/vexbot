import logging

import zmq
import zmq.devices

from vexbot import _get_default_port_config
from vexbot.util.socket_factory import SocketFactory as _SocketFactory

from vexmessage import create_vex_message, decode_vex_message


def _get_address(message: list):
    # Need the address so that we know who to send the message back to
    addresses = []
    # the message is broken by the addresses in the beginning and then the
    # message, like this: `addresses | '' | message `
    for address in message:
        # if we hit a blank string, then we've got all the addresses
        if address == b'':
            break

        addresses.append(address)

    return addresses



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
                                              self.configuration['protocol'])

    def start(self):
        """
        starts/instantiates the messaging
        """
        # alias for pep8 reasons
        create_sock = self._socket_factory.create_socket

        # let's do the sockets that can cause us to exit first
        self.control_socket = create_sock(zmq.ROUTER,
                                          self.configuration['control_port'],
                                          on_error='exit')
        # publish socket is an XSUB socket
        pub_ports = self.configuration['chatter_publish_port']
        self.publish_socket = create_sock(zmq.XSUB,
                                          pub_ports,
                                          on_error='exit')
        # command and control sockets
        self.command_socket = create_sock(zmq.ROUTER,
                                          self.configuration['command_port'])


        self.request_socket = create_sock(zmq.DEALER,
                                          self.configuration['request_port'])

        # subscription socket is a XPUB socket
        sub_ports = self.configuration['chatter_subscription_port']
        self.subscription_socket = create_sock(zmq.XPUB,
                                               sub_ports)


        # control socket address
        self._poller.register(self.command_socket, zmq.POLLIN)
        self._poller.register(self.control_socket, zmq.POLLIN)
        # TODO: verify that dealer sockets are `zmq.POLLOUT` 
        self._poller.register(self.request_socket, zmq.POLLIN)

        # IN type for the poll registration
        self._poller.register(self.subscription_socket, zmq.POLLIN)


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


