import zmq
import time
from threading import Thread

from vexmessage import create_vex_message


class ZmqMessaging:
    def __init__(self,
                 service_name,
                 pub_address=None,
                 sub_address=None,
                 socket_filter=None,
                 heartbeat_address=None):

        self.pub_socket = None
        self.sub_socket = None
        self._heartbeat = None
        self.poller = zmq.Poller()

        self._service_name = service_name
        self._address = {'pub': pub_address,
                         'sub': sub_address,
                         'heart': hearbeat_address}

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
        self._heartbeat = context.socket(zmq.DEALER)
        pub_addr = self._address['pub']
        if pub_addr:
            self.pub_socket.connect(pub_addr)

            if self._socket_filter is not None:
                self.set_socket_filter(self._socket_filter)

        sub_addresses = self._address['sub']
        if sub_addresses:
            for addr in sub_addresses:
                self.sub_socket.connect(addr)
                self.poller.register(self.sub_socket, zmq.POLLIN)

        heart_addr = self._address['heart']
        if heart_addr:
            self._heartbeat.connect(heart_addr)
            self.poller.register(self.sub_socket, zmq.POLLIN)

        self._messaging_started = True

    def update_messaging(self):
        if self._pub_address:
            self.pub_socket.connect(self._pub_address)
        if self._sub_address:
            for s in self._sub_address:
                self.sub_socket.connect(s)
                self.set_socket_filter(self._socket_filter)
        if self._heartbeat._address:
            self._heartbeat._socket.connect(self._heartbeat._address)

    def set_socket_filter(self, filter_):
        self._socket_filter = filter_

        if self.sub_socket:
            self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, filter_)
        if self._heartbeat:
            self._heartbeat.setsockopt_string(zmq.SUBSCRIBE, filter_)

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
