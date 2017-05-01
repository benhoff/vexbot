import sys
import logging

import zmq
import zmq.devices

from vexmessage import create_vex_message, decode_vex_message


class Messaging:
    # TODO: add an `update_messaging` command
    def __init__(self,
                 botname: str='',
                 ip_address: str='',
                 publish_port: int=None,
                 subscribe_port: int=None,
                 heartbeat_port: int=None,
                 control_port: int=None):

        self._service_name = botname
        # Store the addresses of publish, subscription, and heartbeat sockets
        self.address = {'publish': publish_port,
                        'subscriptions': subscribe_port,
                        'heartbeat': heartbeat_port,
                        'control': control_port}

        # The XPub and xSub sockets acts as a pass through
        # they are stored in `socket` since we don't need access to them
        self.socket = {'publish': None,
                       'subscribe': None,
                       'heartbeat': None,
                       'control': None}

        # The subscription socket and publish socket are what the robot uses
        # to communicate. Separate from the proxy XPUB/XSUB
        self.subscription_socket = None
        self.publish_socket = None

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
        self.publish_socket = context.socket(zmq.PUB)

        # Currently reading all messages
        self.subscription_socket = context.socket(zmq.SUB)
        self.subscription_socket.setsockopt(zmq.SUBSCRIBE, b'')
        self._poller.register(self.subscription_socket, zmq.POLLIN)

        # XPUB socket, IN type
        pub = context.socket(zmq.XPUB)
        self._poller.register(pub, zmq.POLLIN)
        self.socket['publish'] = pub

        addresses = self.address['subscriptions']

        if addresses:
            # Can subscribe to multiple addresses
            for addr in addresses:
                try:
                    pub.bind(addr)
                except zmq.error.ZMQError:
                    s = 'Address bind attempt fail. Address tried: {}'
                    s.format(addr)
                    self._logger.error(s)

                # NOTE: still in the for loop here
                self.subscription_socket.connect(addr)

        # XSUB socket, IN type
        sub = context.socket(zmq.XSUB)
        self._poller.register(sub, zmq.POLLIN)
        self.socket['subscribe'] = sub

        sub_addr = self.address['publish']
        if sub_addr:
            try:
                sub.bind(sub_addr)
            except zmq.error.ZMQError:
                self._logger.error('publish address failed. Exiting bot.')
                sys.exit(1)
            self.publish_socket.connect(sub_addr)

        # heartbeat
        heartbeat = context.socket(zmq.ROUTER)
        self._poller.register(heartbeat, zmq.POLLIN)
        self.socket['heartbeat'] = heartbeat

        hb_addr = self.address['heartbeat']
        if hb_addr:
            heartbeat.bind(hb_addr)

    def run(self):
        self.running = True
        pub = self.socket['publish']
        sub = self.socket['subscribe']
        heartbeat = self.socket['heartbeat']

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

            if heartbeat in socks:
                try:
                    msg = heartbeat.recv_multipart(zmq.NOBLOCK)
                    if msg[1] == b'PING':
                        pong_response = [msg[0],
                                         self._service_name.encode('ascii'),
                                         b'PONG']

                        heartbeat.send_multipart(pong_response, zmq.NOBLOCK)
                    elif msg[1] == b'PONG':
                        # TODO: Implement
                        logging.warn('PONG in robot messaging not implemented')
                except zmq.error.Again:
                    pass

            if self.subscription_socket in socks:
                try:
                    msg = self.subscription_socket.recv_multipart(zmq.NOBLOCK)
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
        self.publish_socket.send_multipart(frame)

    def send_command(self, target: str='', **cmd: dict):
        frame = self._create_frame('CMD', target=target, **cmd)
        self.publish_socket.send_multipart(frame)

    def send_response(self, target: str, original: str, **rsp: dict):
        frame = self._create_frame('RSP',
                                   target=target,
                                   original=original,
                                   **rsp)

        self.publish_socket.send_multipart(frame)

    def _create_frame(self, type_, target='', **contents):
        return create_vex_message(target, 'robot', type_, **contents)
