import zmq
import zmq.asyncio

from threading import Thread


class Messaging:
    def __init__(self, context=None):
        self.context = context or zmq.Context()

        self.sub_socket = self.context.socket(zmq.SUB)
        self.sub_socket.setsockopt(zmq.SUBSCRIBE, b'')
        self.pub_socket = self.context.socket(zmq.PUB)

    def send_message(self, message):
        self.pub_socket.send_pyobj(message)

    def subscribe_to_address(self, address):
        self.sub_socket.connect(address)
