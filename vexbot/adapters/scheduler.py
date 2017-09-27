import time
import logging
import zmq as _zmq
from rx.subjects import Subject as _Subject

from vexmessage import decode_vex_message


class Scheduler:
    def __init__(self, messaging):
        """
        """
        self.running = False
        self.messaging = messaging

        self.control = _Subject()
        self.command = _Subject()
        self.subscribe = _Subject()

        # self.request = _Subject()

    def run(self):
        self.running = True
        while self.running:
            try:
                socks = dict(self.messaging.poller.poll())
            except KeyboardInterrupt:
                socks = {}
                self.running = False

            # FIXME: One of these sockets shouldn't be in here
            # Also need to add another
            if self.messaging.control_socket in socks:
                self._control_helper()
            if self.messaging.command_socket in socks:
                self._command_helper()
            if self.messaging.subscription_socket in socks:
                self._subscriber_helper()
            if self.messaging.request_socket in socks:
                self._request_helper()

    def _control_helper(self):
        try:
            msg = self.messaging.control_socket.recv_multipart(_zmq.NOBLOCK)
        except _zmq.error.Again:
            return
        request = self.messaging.handle_raw_command(msg)

        if request is None:
            return

        self.control.on_next(request)

    def _command_helper(self):
        try:
            msg = self.messaging.command_socket.recv_multipart(_zmq.NOBLOCK)
        except _zmq.error.Again:
            return

        request = self.messaging.handle_raw_command(msg)

        if request is None:
            return

        self.command.on_next(request)

    def _subscriber_helper(self):
        try:
            msg = self.messaging.subscription_socket.recv_multipart(_zmq.NOBLOCK)
        except _zmq.error.Again:
            return

        try:
            msg = decode_vex_message(msg)
        except IndexError:
            # TODO: error log? sometimes it's just a subscription notice
            return
        self.subscribe.on_next(msg)

    def _request_helper(self):
        try:
            msg = self.messaging.request_socket.recv_multipart(_zmq.NOBLOCK)
        except _zmq.error.Again:
            return 

        # TODO: Implement
        # request = self.messaging.handle_raw_command(msg)
