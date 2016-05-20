import zmq


class ZmqMessaging:
    def __init__(self, service_name, pub_address=None, sub_address=None):
        self.pub_socket = None
        self.sub_socket = None
        self._socket_identity = None
        self._socket_filter = None

        self._service_name = service_name
        self._pub_address = pub_address
        self._sub_address = sub_address
        self._messaging_started = False
        self._commands = {}

    def start_messaging(self):
        if self._messaging_started:
            self.update_messaging()
            return

        context = zmq.Context()
        self.pub_socket = context.socket(zmq.PUB)
        self.sub_socket = context.socket(zmq.SUB)
        if self._pub_address:
            try:
                self.pub_socket.connect(self._pub_address)
            except zmq.error.ZMQError:
                err = """
                      Incorrect value passed in for socket address in {}, fix it
                      in your settings.yml or default_settings.yml
                      """.format(self._service_name)

                print(err)

            if self._socket_filter is not None:
                self.set_socket_filter(self._socket_filter)


        if self._sub_address:
            self.sub_socket.connect(self._sub_address)
            if self._socket_identity is not None:
                self.set_socket_identity(self._socket_identity)

        self._messaging_started = True

    def update_messaging(self):
        if self._pub_address:
            self.pub_socket.bind(self._pub_address)
        if self._sub_address:
            self.sub_socket.bind(self._sub_address)

    def set_socket_identity(self, id_):
        if self.pub_socket:
            self.pub_socket.set_string(zmq.IDENTITY, id_)
        else:
            self._socket_identity = id_

    def set_socket_filter(self, filter_):
        if self.sub_socket:
            self.sub_socket.set_string(zmq.SUBSCRIBE, filter_)
        else:
            self._socket_filter = filter_

    def send_message(self, *msg):
        msg = list(msg)
        msg.insert(0, self._service_name)
        self.pub_socket.send_pyobj(msg)

    def register_command(self, cmd, function):
        self._commands[cmd] = function

    def is_command(self, cmd):
        callback = self._commands.get(cmd, None)

        if callback:
            callback()
            return True

        return False
