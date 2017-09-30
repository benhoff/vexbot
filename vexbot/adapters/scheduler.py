import time
import logging
import types

import zmq as _zmq
from zmq.eventloop import IOLoop
from zmq.eventloop.zmqstream import ZMQStream
from rx.subjects import Subject as _Subject

from vexmessage import decode_vex_message


class Scheduler:
    def __init__(self, messaging):
        """
        """
        self.running = False
        self.messaging = messaging
        self.loop = IOLoop()

        self._request = None
        self._command = None
        self._control = None
        self._subscribe = None

        self.control = _Subject()
        self.command = _Subject()
        self.subscribe = _Subject()

    def add_callback(self, callback, *args, **kwargs):
        self.loop.add_callback(callback, *args, **kwargs)

    def setup(self):
        self._request = ZMQStream(self.messaging.request_socket, self.loop)
        self._command = ZMQStream(self.messaging.command_socket, self.loop)
        self._control = ZMQStream(self.messaging.control_socket, self.loop)
        self._subscribe = ZMQStream(self.messaging.subscription_socket,
                                    self.loop)

        self._command.on_recv(self._command_helper)
        self._request.on_recv(self._request_helper)
        self._subscribe.on_recv(self._subscriber_helper)
        self._control.on_recv(self._control_helper)

    def _control_helper(self, msg):
        request = self.messaging.handle_raw_command(msg)

        if request is None:
            return

        self.control.on_next(request)

    def _command_helper(self, msg):
        request = self.messaging.handle_raw_command(msg)

        if request is None:
            return

        self.command.on_next(request)

    def _subscriber_helper(self, msg):
        # TODO: error log? sometimes it's just a subscription notice
        if len(msg) == 1:
            return

        msg = decode_vex_message(msg)
        self.subscribe.on_next(msg)

    def _request_helper(self, msg):
        pass
