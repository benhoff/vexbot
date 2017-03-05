import zmq

from vexmessage import create_vex_message, decode_vex_message


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
        self._pong_callback = None
        self.poller = zmq.Poller()

        self._service_name = service_name
        self._address = {'pub': pub_address,
                         'sub': sub_address,
                         'heart': heartbeat_address}

        self._socket_filter = socket_filter
        self._messaging_started = False
        try:
            import setproctitle
            if service_name:
                setproctitle.setproctitle(service_name)
        except ImportError:
            pass

    def set_pong_callback(self, function):
        self._pong_callback = function

    def _handle_pong(self, sender: str):
        if self._pong_callback is not None:
            self._pong_callback(sender)

    def run(self, timeout=None):
        while True:
            socks = dict(self.poller.poll(timeout))
            if self._heartbeat in socks:
                try:
                    msg = self._heartbeat.recv_multipart(zmq.NOBLOCK)
                    if msg[1] == b'PING':
                        pong_response = [msg[0],
                                         self._service_name.encode('ascii'),
                                         b'PONG']

                        self._heartbeat.send_multipart(pong_response)
                    elif msg[1] == b'PONG':
                        self._handle_pong(msg[0].decode('ascii'))
                except zmq.error.Again:
                    pass
            if self.sub_socket in socks:
                try:
                    msg = self.sub_socket.recv_multipart(zmq.NOBLOCK)
                    try:
                        yield decode_vex_message(msg)
                    except Exception:
                        pass
                except zmq.error.Again:
                    pass

    def start_messaging(self):
        if self._messaging_started:
            self.update_messaging()
            return

        context = zmq.Context()

        pub_addr = self._address['pub']
        self.pub_socket = context.socket(zmq.PUB)
        if pub_addr:
            self.pub_socket.connect(pub_addr)

        sub_addresses = self._address['sub']
        self.sub_socket = context.socket(zmq.SUB)
        self.poller.register(self.sub_socket, zmq.POLLIN)
        if sub_addresses:
            for addr in sub_addresses:
                self.sub_socket.connect(addr)

        heart_addr = self._address['heart']
        self._heartbeat = context.socket(zmq.DEALER)
        self.poller.register(self._heartbeat, zmq.POLLIN)

        if self._socket_filter is not None:
            self.set_socket_filter(self._socket_filter)
            self._heartbeat.setsockopt_string(zmq.IDENTITY,
                                              self._socket_filter)

        if heart_addr:
            self._heartbeat.connect(heart_addr)

        self._messaging_started = True

    def update_messaging(self,
                         pub_address=None,
                         sub_addresses=None,
                         heartbeat_address=None,
                         disconnect_old_addr=True):

        # if not self._messaging_started:
        #    self.start_messaging()

        if pub_address:
            if disconnect_old_addr:
                self.disconnect_pub_socket(self._address['pub'])

            self.pub_socket.connect(pub_address)
            self._address['pub'] = pub_address

        if sub_addresses:
            if disconnect_old_addr:
                self.disconnect_sub_socket(self._address['sub'])
            for s in sub_addresses:
                self.sub_socket.connect(s)
            self._address['sub'] = sub_addresses

        if heartbeat_address:
            if disconnect_old_addr:
                self.disconnect_heartbeat_socket(self._address['heart'])
            self._heartbeat.connect(heartbeat_address)
            self._address['heart'] = heartbeat_address

    def set_socket_filter(self, filter_):
        self._socket_filter = filter_

        if self.sub_socket:
            self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, filter_)

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

    def send_ping(self):
        # TODO: Think about putting a service here?
        self._heartbeat.send(b'PING')

    def disconnect_sub_socket(self, addresses=None):
        if addresses is None:
            addresses = self._address['sub']

        if not addresses:
            return
        for addr in addresses:
            self.sub_socket.disconnect(addr)

    def disconnect_heartbeat_socket(self, address=None):
        self._disconnect_socket(self._heartbeat, 'heart', address)

    def disconnect_pub_socket(self, address=None):
        self._disconnect_socket(self.pub_socket, 'pub', address)

    def _disconnect_socket(self, socket, socket_name, address=None):
        if address is None:
            address = self._address[socket_name]

        # can have `None` for value
        if not address:
            return
        try:
            socket.disconnect(address)
        except zmq.error.ZMQError:
            pass

        self._address[socket_name] = None
