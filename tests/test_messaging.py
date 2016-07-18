import unittest
from time import sleep

import zmq
from vexmessage import decode_vex_message
from vexbot.messaging import Messaging


class TestMessaging(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        self.subscribe_address = 'tcp://127.0.0.1:4006'
        self.publish_address = 'tcp://127.0.0.1:4007'
        self.settings = {'subscribe_address': self.subscribe_address,
                         'publish_address': self.publish_address}

        context = zmq.Context()
        self.messaging = Messaging(self.settings, context)

        self.test_publish_socket = context.socket(zmq.PUB)
        self.test_publish_socket.connect(self.publish_address)

        self.test_subscribe_socket = context.socket(zmq.SUB)
        self.test_subscribe_socket.connect(self.subscribe_address)
        self.test_subscribe_socket.setsockopt_string(zmq.SUBSCRIBE, '')
        sleep(.2)
        super().__init__(*args, **kwargs)

    """
    def test_send_message(self):
        self.messaging.send_message('', test='blue')
        frame = self.test_subscribe_socket.recv_multipart()
        message = decode_vex_message(frame)
        self.assertEqual(message.target, '')
        self.assertEqual(message.source, 'robot')
        self.assertEqual(message.contents['test'], 'blue')
        self.assertEqual(message.type, 'MSG')
    """

    def test_send_targeted_message(self):
        self.test_subscribe_socket.setsockopt_string(zmq.SUBSCRIBE, 'test')
        self.messaging.send_message('test', test='blue')
        frame = self.test_subscribe_socket.recv_multipart()
        message = decode_vex_message(frame)
        self.assertEqual(message.target, 'test')
        self.assertEqual(message.source, 'robot')
        self.assertEqual(message.contents['test'], 'blue')
        self.assertEqual(message.type, 'MSG')
