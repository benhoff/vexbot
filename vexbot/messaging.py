import zmq
import zmq.asyncio

from threading import Thread


class Messaging:
    def __init__(self, settings, context=None):
        context = context or zmq.Context()

        self._proxy = zmq.devices.ThreadProxy(zmq.XSUB, zmq.XPUB)
        proxy_address = settings.get('proxy_address',
                                     'tcp://127.0.0.1:4002')

        subscribe_address = settings.get('subscribe_address',
                                         'tcp://127.0.0.1:4000')

        publish_address = settings.get('publish_address',
                                       'tcp://127.0.0.1:4001')

        self._proxy.bind_in(subscribe_address)
        self._proxy.bind_out(publish_address)

        self._proxy.bind_mon(proxy_address)

        self._monitor_socket = context.socket(zmq.SUB)
        # self._monitor_socket.setsockopt(zmq.SUBSCRIBE, name)
        self._monitor_socket.setsockopt(zmq.SUBSCRIBE, b'')
        self._monitor_socket.connect(proxy_address)

        self._publish_socket = context.socket(zmq.PUB)
        # self._publish_socket.setsockopt(zmq.IDENTITY, name)
        self._publish_socket.connect(publish_address)

        self._proxy.start()
