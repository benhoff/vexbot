import zmq
import zmq.devices

from vexmessage import create_vex_message


class Messaging:
    # TODO: add an `update_messaging` command
    def __init__(self,
                 context,
                 publish_address=None,
                 subscribe_address=None,
                 monitor_address=None):

        # FIXME: naming convetion?
        self._service_name = context
        self._proxy = None
        self._messaging_started = False
        self._publish_address = publish_address
        self._subscribe_address = subscribe_address
        self._monitor_address = monitor_address

    def _try_bind(self, function_call, address):
        """
        Try bind only binds if bool(address) is True
        Does a try/except around the method call
        """
        if address:
            try:
                function_call(address)
            except zmq.error.ZMQError:
                err = """
                      Incorrect value passed in for socket address in {}, fix
                      it in your settings.yml or default_settings.yml
                      """.format(self._service_name)

                # TODO: use log module instead of print
                print(err)

    def start(self, zmq_context=None):
        context = zmq_context or zmq.Context()

        self._proxy = zmq.devices.ThreadProxy(zmq.XSUB, zmq.XPUB)

        self._try_bind(self._proxy.bind_in, self._publish_address)
        self._try_bind(self._proxy.bind_out, self._subscribe_address)
        self._try_bind(self._proxy.bind_mon, self._monitor_address)

        self.subscription_socket = context.socket(zmq.SUB)
        self.subscription_socket.setsockopt(zmq.SUBSCRIBE, b'')
        self.subscription_socket.connect(subscribe_address)

        self._proxy.start()
        self.publish_socket = context.socket(zmq.PUB)
        self.publish_socket.connect(publish_address)

    def subscription_active(self):
        # FIXME: add in actual parsing
        return True

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
