import sys
import logging

import zmq
import zmq.devices

from vexmessage import create_vex_message, decode_vex_message


class Messaging:
    # TODO: add an `update_messaging` command
    def __init__(self, botname: str='', **kwargs):
        """
        `protocol`   'tcp'
        `ip_address` '127.0.0.1'
        `command_publish_port` 4000
        `command_subscribe_port` 4001
        `heartbeat_port` 4002
        `control_port` 4003
        """
        # Defaults. Can be overriden by the use of `kwargs`
        configuration = {'protocol': 'tcp',
                         'ip_address': '127.0.0.1',
                         'command_publish_port': 4000,
                         'command_subscribe_port': [4001,],
                         'heartbeat_port': 4002,
                         'control_port': 4003}

        # override the default with the `kwargs`
        configuration.update(kwargs)

        self._service_name = botname
        self.protocol = configuration['protocol']
        self.ip_address = configuration['ip_address']
        self._zmq_address_format = '{}://{}:{}'
        # Store the addresses of publish, subscription, and heartbeat sockets
        self.address = {'publish': configuration['command_publish_port'],
                        'subscriptions': configuration['command_subscribe_port'],
                        'heartbeat': configuration['heartbeat_port'],
                        'control': configuration['control_port']}

        # The XPub and xSub sockets acts as a pass through
        # they are stored in `socket` since we don't need access to them
        self.socket = {'publish': None,
                       'subscribe': None,
                       'heartbeat': None,
                       'control': None}

        # The subscription socket and publish socket are what the robot uses
        # to communicate. Separate from the proxy XPUB/XSUB
        self.command_subscription_socket = None
        self.commmand_publish_socket = None

        # The poller polls each socket
        self._poller = zmq.Poller()
        self.running = False
        self._logger = logging.getLogger(__name__)

    def start(self, zmq_context: 'zmq.Context'=None):
        """
        starts/instantiates the messaging
        """
        context = zmq_context or zmq.Context()

        # Publish socket managed by robot
        self.command_publish_socket = context.socket(zmq.PUB)

        # Currently reading all messages
        self.command_subscription_socket = context.socket(zmq.SUB)
        self.command_subscription_socket.setsockopt(zmq.SUBSCRIBE, b'')
        self._poller.register(self.command_subscription_socket, zmq.POLLIN)

        # XPUB socket, IN type
        pub = context.socket(zmq.XPUB)
        self._poller.register(pub, zmq.POLLIN)
        self.socket['publish'] = pub

        addresses = self.address['subscriptions']

        if addresses:
            # Can subscribe to multiple addresses
            for addr in addresses:
                try:
                    ip_address = self._zmq_address_format.format(self.protocol,
                                                                 self.ip_address,
                                                                 addr)

                    pub.bind(ip_address)
                except zmq.error.ZMQError:
                    s = 'Address bind attempt fail. Address tried: {}'
                    s = s.format(ip_address)
                    self._logger.error(s)

                # NOTE: still in the for loop here
                self.command_subscription_socket.connect(ip_address)

        # XSUB socket, IN type
        sub = context.socket(zmq.XSUB)
        self._poller.register(sub, zmq.POLLIN)
        self.socket['subscribe'] = sub

        sub_addr = self.address['publish']
        sub_addr = self._zmq_address_format.format(self.protocol, self.ip_address, sub_addr)
        if sub_addr:
            try:
                sub.bind(sub_addr)
            except zmq.error.ZMQError:
                self._logger.error('publish address failed. Exiting bot.')
                sys.exit(1)
            self.command_publish_socket.connect(sub_addr)

        # heartbeat
        heartbeat = context.socket(zmq.ROUTER)
        self._poller.register(heartbeat, zmq.POLLIN)
        self.socket['heartbeat'] = heartbeat

        hb_addr = self.address['heartbeat']
        hb_addr = self._zmq_address_format.format(self.protocol, self.ip_address, hb_addr)
        if hb_addr:
            heartbeat.bind(hb_addr)

    def run(self):
        self.running = True
        pub = self.socket['publish']
        sub = self.socket['subscribe']

        while True:
            socks = dict(self._poller.poll(timeout=500))
            if sub in socks:
                try:
                    msg = sub.recv_multipart(zmq.NOBLOCK)
                    pub.send_multipart(msg)
                except zmq.error.Again:
                    pass
            if pub in socks:
                try:
                    msg = pub.recv_multipart(zmq.NOBLOCK)
                    sub.send_multipart(msg)
                except zmq.error.Again:
                    pass

            if self.command_subscription_socket in socks:
                try:
                    msg = self.command_subscription_socket.recv_multipart(zmq.NOBLOCK)
                    try:
                        msg = decode_vex_message(msg)
                    # TODO: error handeling
                    except Exception as e:
                        pass
                    else:
                        yield msg
                except zmq.error.Again:
                    pass

    def send_message(self, target: str='', **msg: dict):
        frame = self._create_frame('MSG', target=target, **msg)
        self.command_publish_socket.send_multipart(frame)

    def send_command(self, target: str='', **cmd: dict):
        frame = self._create_frame('CMD', target=target, **cmd)
        self.command_publish_socket.send_multipart(frame)

    def send_response(self, target: str, original: str, **rsp: dict):
        frame = self._create_frame('RSP',
                                   target=target,
                                   original=original,
                                   **rsp)

        self.command_publish_socket.send_multipart(frame)

    def _create_frame(self, type_, target='', **contents):
        return create_vex_message(target, self._service_name, type_, **contents)
