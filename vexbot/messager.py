import zmq
import zmq.asyncio

from threading import Thread


class Messager:
    def __init__(self, context=None):
        self.context = context or zmq.Context()

        self.sub_socket = self.context.socket(zmq.SUB)
        self.sub_socket.setsockopt(zmq.SUBSCRIBE, b'')
        self.thread = Thread(target=self.run, daemon=True)

    def subscribe_to_address(self, address):
        self.sub_socket.connect(address)

    def run(self):
        while True:
            frame = self.sub_socket.recv()
            # do some really cool parsing here
            print(frame)
