import zmq as _zmq
from zmq.eventloop import IOLoop
from zmq.eventloop.zmqstream import ZMQStream
from rx.subjects import Subject as _Subject

from vexmessage import decode_vex_message


class Scheduler:
    def __init__(self, messaging):
        """
        """
        self.messaging = messaging

        self._control = None
        self._command = None
        self._publish = None
        self._request = None
        self._subscribe = None

        self.control = _Subject()
        self.command = _Subject()
        self.subscribe = _Subject()
        self.loop = IOLoop()

    def setup(self):
        self._control = ZMQStream(self.messaging.control_socket, self.loop)
        self._command = ZMQStream(self.messaging.command_socket, self.loop)
        self._publish = ZMQStream(self.messaging.publish_socket, self.loop)
        self._request = ZMQStream(self.messaging.request_socket, self.loop)
        self._subscribe = ZMQStream(self.messaging.subscription_socket,
                                    self.loop)

        self._command.on_recv(self._command_helper)
        self._request.on_recv(self._request_helper)
        self._subscribe.on_recv(self._subscriber_helper)
        self._control.on_recv(self._control_helper)
        self._publish.on_recv(self._publish_helper)

    def run(self):
        return self.loop.start()

    def add_callback(self, callback, *args, **kwargs):
        self.loop.add_callback(callback, *args, **kwargs)

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

    def _publish_helper(self, msg):
        self.loop.add_callback(self.messaging.subscription_socket.send_multipart, msg)
        msg = decode_vex_message(msg)
        self.subscribe.on_next(msg)

    def _subscriber_helper(self, msg):
        self.loop.add_callback(self.messaging.publish_socket.send_multipart, msg)

    def _request_helper(self, msg):
        print(msg)
