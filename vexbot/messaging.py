import zmq
import zmq.asyncio

from threading import Thread


class Messaging:
    def __init__(self, context=None, pub_socket='tcp://127.0.0.1:5556'):
        self.context = context or zmq.Context()

        self.sub_socket = self.context.socket(zmq.SUB)
        self.sub_socket.setsockopt(zmq.SUBSCRIBE, b'')
        self.pub_socket = self.context.socket(zmq.PUB)
        self.pub_socket.bind(pub_socket)
        # self.thread = Thread(target=self.run, daemon=True)

    def subscribe_to_address(self, address):
        self.sub_socket.connect(address)
