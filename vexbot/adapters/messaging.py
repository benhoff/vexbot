import zmq
import time
from threading import Thread

from vexmessage import create_vex_message


class _HeartbeatListener:
    def __init__(self, address, interval=2):
        self._address = address
        self._socket = None
        self._thread = None

        self.interval = interval
        self._time = None
        self.listening = False

        self._false_callback = None
        self._true_callback = None

    def start_messaging(self, context=None):
        context = context or zmq.Context()
        self._socket = context.socket(zmq.SUB)
        self._socket.setsockopt(zmq.SUBSCRIBE, b'')
        # dirty hack to make sure the robot is really alive
        self._time = time.time() - 10
        if self._address:
            self._socket.connect(self._address)

    def listen_for_heartbeats(self):
        self._thread = Thread(target=self._heartbeat_loop)
        self._thread.daemon = True
        self._thread.start()
        self.listening = True

    def set_false_callback(self, callback):
        self._false_callback = callback

    def set_true_callback(self, callback):
        self._true_callback = callback

    def _heartbeat_loop(self):
        while True:
            time_delta = time.time() - self._time
            alive = time_delta < self.interval

            if alive:
                if self._true_callback:
                    self._true_callback()
            else:
                if self._false_callback:
                    self._false_callback()

            if self._address:
                try:
                    msg = self._socket.recv(flags=zmq.NOBLOCK)
                    self._time = time.time()
                except zmq.Again:
                    pass
                time.sleep(.5)
            else:
                time.sleep(2)


class ZmqMessaging:
    def __init__(self,
                 service_name,
                 pub_address=None,
                 sub_address=None,
                 socket_filter=None,
                 heartbeat_address=None):

        self.pub_socket = None
        self.sub_socket = None

        self._service_name = service_name
        self._pub_address = pub_address
        self._sub_address = sub_address
        self._socket_filter = socket_filter
        self._heartbeat = _HeartbeatListener(heartbeat_address)

        self._messaging_started = False
        try:
            import setproctitle
            if service_name:
                setproctitle.setproctitle(service_name)
        except ImportError:
            pass

    def start_messaging(self):
        if self._messaging_started:
            # TODO: apply to heartbeat
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
            for addr in self._sub_address:
                self.sub_socket.connect(addr)

        self._heartbeat.start_messaging(context)
        self._messaging_started = True

    def listen_for_heartbeats(self):
        if self._heartbeat.listening:
            return

        self._heartbeat.listen_for_heartbeats()

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
