import zmq
import zmq.devices

from vexmessage import create_vex_message


class Messaging:
    def __init__(self, settings, context=None):
        self._service_name = b'robot'
        context = context or zmq.Context()

        self._proxy = zmq.devices.ThreadProxy(zmq.XSUB, zmq.XPUB)
        proxy_address = settings.get('proxy_address',
                                     'tcp://127.0.0.1:4002')

        subscribe_address = settings.get('subscribe_address',
                                         'tcp://127.0.0.1:4000')

        publish_address = settings.get('publish_address',
                                       'tcp://127.0.0.1:4001')

        self._proxy.bind_in(publish_address)
        self._proxy.bind_out(subscribe_address)
        self._proxy.bind_mon(proxy_address)

        self.subscription_socket = context.socket(zmq.SUB)
        self.subscription_socket.setsockopt(zmq.SUBSCRIBE, b'')
        self.subscription_socket.connect(subscribe_address)

        self._proxy.start()
        self.publish_socket = context.socket(zmq.PUB)
        self.publish_socket.connect(publish_address)

    def _create_frame(self, type, *contents, target=''):
        return create_vex_message(target, 'robot', type, contents)

    def send_message(self, *msg, target=''):
        frame = self._create_frame('MSG', *msg, target=target)
        self.publish_socket.send_multipart(frame)

    def send_command(self, *cmd, target=''):
        frame = self._create_frame('CMD', *cmd, target=target)
        self.publish_socket.send_multipart(frame)

    def send_response(self, *rsp, target, original):
        # FIXME: fix hack to insert original in first index
        frame = self._create_frame('RSP',
                                   *(original, *rsp),
                                   target=target)

        self.publish_socket.send_multipart(frame)
