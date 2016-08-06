import zmq
import zmq.devices

from vexmessage import create_vex_message


class Messaging:
    def __init__(self, settings, context=None):
        self._service_name = b'robot'
        context = context or zmq.Context()

        self._proxy = zmq.devices.ThreadProxy(zmq.XSUB, zmq.XPUB)
        proxy_address = settings.get('monitor_address')
        subscribe_address = settings.get('subscribe_address')
        publish_address = settings.get('publish_address')

        self._proxy.bind_in(publish_address)
        self._proxy.bind_out(subscribe_address)
        self._proxy.bind_mon(proxy_address)

        self.subscription_socket = context.socket(zmq.SUB)
        self.subscription_socket.setsockopt(zmq.SUBSCRIBE, b'')
        self.subscription_socket.connect(subscribe_address)

        self._proxy.start()
        self.publish_socket = context.socket(zmq.PUB)
        self.publish_socket.connect(publish_address)

    def _create_frame(self, type, target='', **contents):
        return create_vex_message(target, 'robot', type, **contents)

    def send_message(self, target='', **msg):
        frame = self._create_frame('MSG', target=target, **msg)
        self.publish_socket.send_multipart(frame)

    def send_command(self, target='', **cmd):
        frame = self._create_frame('CMD', target=target, **cmd)
        self.publish_socket.send_multipart(frame)

    def send_response(self, target, original, **rsp):
        frame = self._create_frame('RSP',
                                   target=target,
                                   original=original,
                                   **rsp)

        self.publish_socket.send_multipart(frame)
