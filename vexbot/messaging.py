import os
import sys
import time
import traceback
import logging
from threading import Thread

import zmq
import zmq.devices

from vexmessage import create_vex_message


class Messaging:
    # TODO: add an `update_messaging` command
    def __init__(self,
                 context,
                 publish_address=None,
                 subscribe_address=None,
                 heartbeat_address=None):

        self._service_name = context
        self._proxy = None
        self._messaging_started = False
        self._types = ['publish', 'subscribe', 'heartbeat']
        self.address = {'publish': publish_address,
                        'subscriptions': subscribe_address,
                        'heartbeat': heartbeat_address}

        # NOTE: Subscription socket managed by robot NOT tracked here
        self.socket = {'publish': None,
                       'subscribe': None,
                       'heartbeat': None}

        self._poller = zmq.Poller()
        self.subscription_socket = None
        self.publish_socket = None
        self._thread = None
        self.running = False

    def start(self, zmq_context=None):
        context = zmq_context or zmq.Context()

        # subscription & publish socket managed by robot
        self.subscription_socket = context.socket(zmq.SUB)
        self.subscription_socket.setsockopt(zmq.SUBSCRIBE, b'')
        self.publish_socket = context.socket(zmq.PUB)

        self._poller = zmq.Poller()

        # out type
        pub = context.socket(zmq.XPUB)
        addresses = self.address['subscriptions']
        if addresses:
            for addr in addresses:
                pub.bind(addr)
                self.subscription_socket.connect(addr)

        self.socket['publish'] = pub
        self._poller.register(pub, zmq.POLLOUT)

        # in type
        sub = context.socket(zmq.XSUB)
        sub_addr = self.address['publish']
        if sub_addr:
            sub.bind(sub_addr)
            self.publish_socket.connect(sub_addr)

        self.socket['subscribe'] = sub
        self._poller.register(sub, zmq.POLLIN)

        # heartbeat
        heartbeat = context.socket(zmq.PUB)
        hb_addr = self.address['heartbeat']
        if hb_addr:
            heartbeat.bind(hb_addr)

        self.socket['heartbeat'] = heartbeat
        self._poller.register(heartbeat, zmq.POLLOUT)

        def run():
            self.running = True
            time_start = time.time()
            while True:
                socks = dict(self._poller.poll(500))
                if sub in socks:
                    pub.send(sub.recv(zmq.NOBLOCK))
                time_now = time.time()
                time_delta = time_now - time_start
                if time_delta > 0.75:
                    heartbeat.send(b'', zmq.NOBLOCK)
                    time_start = time_now

        self._thread = Thread(target=run)
        self._thread.daemon = True
        self._thread.start()

    def subscription_active(self):
        # FIXME: add in actual parsing
        return True

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
