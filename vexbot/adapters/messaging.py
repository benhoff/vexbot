import zmq

from vexmessage import create_vex_message


class ZmqMessaging:
    def __init__(self,
                 service_name,
                 pub_address=None,
                 sub_address=None,
                 socket_filter=None):

        self.pub_socket = None
        self.sub_socket = None

        self._service_name = service_name
        self._pub_address = pub_address
        self._sub_address = sub_address
        self._socket_filter = socket_filter

        self._messaging_started = False
        try:
            import setproctitle
            if service_name:
                setproctitle.setproctitle(service_name)
        except ImportError:
            pass

    def start_messaging(self):
        if self._messaging_started:
            self.update_messaging()
            return

        context = zmq.Context()
        self.pub_socket = context.socket(zmq.PUB)
        self.sub_socket = context.socket(zmq.SUB)
        if self._pub_address:
            self.pub_socket.connect(self._pub_address)

            if self._socket_filter is not None:
                self.set_socket_filter(self._socket_filter)

        if self._sub_address:
            self.sub_socket.connect(self._sub_address)

        self._messaging_started = True

    def update_messaging(self):
        # FIXME: need to disconnect first?
        if self._pub_address:
            self.pub_socket.bind(self._pub_address)
        if self._sub_address:
            self.sub_socket.bind(self._sub_address)

    def set_socket_filter(self, filter_):
        if self.sub_socket:
            self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, filter_)
        else:
            self._socket_filter = filter_

    def send_message(self, target='', **msg):
        frame = create_vex_message(target, self._service_name, 'MSG', **msg)
        self.pub_socket.send_multipart(frame)

    def send_status(self, status, target='', **kwargs):
        frame = create_vex_message(target,
                                   self._service_name,
                                   'STATUS',
                                   status=status,
                                   **kwargs)

        self.pub_socket.send_multipart(frame)

    def send_command(self, target='', **command):
        frame = create_vex_message(target,
                                   self._service_name,
                                   'CMD',
                                   **command)

        self.pub_socket.send_multipart(frame)
