import sys
import time
import logging
from contextlib import ContextDecorator

import zmq
import zmq.devices

from vexmessage import create_vex_message, decode_vex_message


class Messaging:
    # TODO: add an `update_messaging` command
    def __init__(self,
                 context,
                 publish_address=None,
                 subscribe_address=None,
                 heartbeat_address=None):

        self._service_name = context
        self.address = {'publish': publish_address,
                        'subscriptions': subscribe_address,
                        'heartbeat': heartbeat_address}

        self.subscription_socket = None
        self.publish_socket = None

        # NOTE: Since Sub & Pub socket managed by robot
        # NOT tracked here in self.socket
        self.socket = {'publish': None,
                       'subscribe': None,
                       'heartbeat': None}

        self._poller = zmq.Poller()
        self.running = False

    def start(self, zmq_context=None):
        context = zmq_context or zmq.Context()

        # Publish socket managed by robot
        self.publish_socket = context.socket(zmq.PUB)

        self._poller = zmq.Poller()

        self.subscription_socket = context.socket(zmq.SUB)
        self.subscription_socket.setsockopt(zmq.SUBSCRIBE, b'')
        self._poller.register(self.subscription_socket, zmq.POLLIN)

        # XPUB socket, IN type
        pub = context.socket(zmq.XPUB)
        addresses = self.address['subscriptions']

        if addresses:
            for addr in addresses:
                try:
                    pub.bind(addr)
                except zmq.error.ZMQError:
                    pass

                # NOTE: still in the for loop here
                self.subscription_socket.connect(addr)

        self.socket['publish'] = pub
        self._poller.register(pub, zmq.POLLIN)

        # XSUB socket, IN type
        sub = context.socket(zmq.XSUB)
        sub_addr = self.address['publish']
        if sub_addr:
            try:
                sub.bind(sub_addr)
            except zmq.error.ZMQError:
                sys.exit(1)
            self.publish_socket.connect(sub_addr)

        self.socket['subscribe'] = sub
        self._poller.register(sub, zmq.POLLIN)

        # heartbeat
        heartbeat = context.socket(zmq.ROUTER)
        hb_addr = self.address['heartbeat']
        if hb_addr:
            heartbeat.bind(hb_addr)

        self.socket['heartbeat'] = heartbeat
        self._poller.register(heartbeat, zmq.POLLIN)

    def run(self):
        self.running = True
        pub = self.socket['publish']
        sub = self.socket['subscribe']
        heartbeat = self.socket['heartbeat']

        while True:
            socks = dict(self._poller.poll(timeout=500))
            socks = dict(socks)
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
                    heartbeat.send_multipart([msg[0], b''], zmq.NOBLOCK)
                except zmq.error.Again:
                    pass

            if self.subscription_socket in socks:
                try:
                    msg = self.subscription_socket.recv_multipart(zmq.NOBLOCK)
                    try:
                        msg = decode_vex_message(msg)
                    except Exception:
                        pass
                    else:
                        yield msg
                except zmq.error.Again:
                    pass

    def _create_frame(self, type, target='', **contents):
        return create_vex_message(target, 'robot', type, **contents)

    def send_message(self, target='', **msg):
        frame = self._create_frame('MSG', target=target, **msg)
        self.publish_socket.send_multipart(frame)

    def send_command(self, target='', **cmd):
        frame = self._create_frame('CMD', target=target, **cmd)
        self.publish_socket.send_multipart(frame)

    def send_response(self, target, original, **rsp):
        frame = self._create_frame('RSP',
                                   target=target,
                                   original=original,
                                   **rsp)

        self.publish_socket.send_multipart(frame)
