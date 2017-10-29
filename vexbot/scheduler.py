from zmq.eventloop.zmqstream import ZMQStream


class Scheduler:
    def __init__(self):
        # NOTE: This will probably go into the SocketFactory
        self._streams = []

    def register_socket(self, socket, loop, on_recv):
        stream = ZMQStream(socket, loop)
        stream.on_recv(on_recv)
        self._streams.append(stream)
