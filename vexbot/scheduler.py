from rx.subjects import Subject as _Subject


class Scheduler:
    def __init__(self, messaging):
        """
        """
        self.running = False
        self.messaging = messaging

        self.control = _Subject()
        self.command = _Subject()
        self.subscribe = _Subject()

    def _control_helper(self):
        try:
            msg = self.messaging.control_socket.recv_multipart(zmq.NOBLOCK)
        except zmq.error.Again:
            return
        request = self.messaging.handle_raw_command(msg)
        self.control.on_next(request)

    def _command_helper(self):
        try:
            msg = self.messaging.command_socket.recv_multipart(zmq.NOBLOCK)
        except zmq.error.Again:
            return

        request = self.messaging.handle_raw_command(msg)
        self.command.on_next(request)

    def _publish_helper(self):
        try:
            msg = self.messaging.publish_socket.recv_multipart(zmq.NOBLOCK)
        except zmq.error.Again:
            return

        self.messaging.subscription_socket.send_multipart(msg)

    def _subscriber_helper(self):
        try:
            msg = self.messaging.subscription_socket.recv_multipart(zmq.NOBLOCK)
        except zmq.error.Again:
            return

        self.messaging.publish_socket.send_multipart(msg)
        msg = decode_vex_message(msg)
        self.subscribe.on_next(msg)

    def _request_helper(self):
        try:
            msg = self.messaging.request_socket.recv_multipart(zmq.NOBLOCK)
        except zmq.error.Again:
            return 

        # TODO: Implement
        # request = self.messaging.handle_raw_command(msg)

    def run(self):
        self.running = True
        while self.running:
            try:
                socks = dict(self.messaging._poller.poll())
            except KeyboardInterrupt:
                socks = {}
                self.running = False

            if self.messaging.control_socket in socks:
                self._control_helper()
            if self.messaging.command_socket in socks:
                self._command_helper()
            if self.messaging.publish_socket in socks:
                self._publish_helper()
            if self.messaging.subscription_socket in socks:
                self._subscriber_helper()
            if self.messaging.request_socket in socks:
                self._request_helper()
