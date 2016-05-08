import zmq


class ZmqMessaging:
    def __init__(self, service_name, pub_address=None, sub_address=None):
        self._service_name = service_name
        self.pub_socket = None
        self.sub_socket = None
        self.sub_address = sub_address
        self.pub_address = pub_address
        self._messaging_started = False

    def start_messaging(self):
        if self._messaging_started:
            self.update_messaging()
            return

        context = zmq.Context()
        self.pub_socket = context.socket(zmq.PUB)
        if self.pub_address:
            try:
                self.pub_socket.bind(self.pub_address)
            except zmq.error.ZMQError:
                err = """
                      Incorrect value passed in for socket address in {}, fix it
                      in your settings.yml or default_settings.yml
                      """.format(self._service_name)

                print(err)

        self.sub_socket = context.socket(zmq.SUB)
        if self.sub_address:
            self.sub_socket.connect(self.sub_address)
            self.sub_socket.setsockopt(zmq.SUBSCRIBE, b'')

        self._messaging_started = True

    def update_messaging(self):
        if self.pub_address:
            self.pub_socket.bind(self.pub_address)
        if self.sub_address:
            self.sub_socket.bind(self.sub_address)

    def send_message(self, *msg):
        msg = list(msg)
        msg.insert(0, self._service_name)
        self.pub_socket.send_pyobj(msg)
