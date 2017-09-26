import zmq
import logging
import pickle

from vexbot import _get_default_port_config
from vexbot.util.socket_factory import SocketFactory as _SocketFactory

from vexmessage import create_vex_message, decode_vex_message


class Messaging:
    def __init__(self, service_name: str, socket_filter: str='', **kwargs):
        """
        `kwargs`:
            protocol:   'ipc'
            ip_address: '127.0.0.1'
            chatter_publish_port: 4000
            chatter_subscription_port: [4001,]
            command_port: 4002
            request_port: 4003
            control_port: 4005
        """
        # Get the default port configurations
        configuration = _get_default_port_config()
        # update the default port configurations with the kwargs
        configuration.update(kwargs)
        self.publish_socket = None
        self.subscription_socket = None
        self.command_socket = None
        self.control_socket = None
        self.request_socket = None

        self._pong_callback = None
        self.poller = zmq.Poller()

        # store the service name and the configuration
        self._service_name = service_name
        self._configuration = configuration

        self._socket_filter = socket_filter
        self._messaging_started = False
        self._logger = logging.getLogger(self._service_name)

        self._socket_factory = _SocketFactory(configuration['ip_address'],
                                              configuration['protocol'],
                                              logger=self._logger)


        try:
            import setproctitle
            setproctitle.setproctitle(self._service_name)
        except ImportError:
            pass

    def set_pong_callback(self, function):
        self._pong_callback = function

    def _handle_pong(self, sender: str):
        if self._pong_callback is not None:
            self._pong_callback(sender)

    def run(self, timeout=None):
        while True:
            socks = dict(self.poller.poll(timeout))
            if self.command_socket in socks:
                msg = self.command_socket.recv_multipart()
                if msg[0] == b'PONG':
                    self._handle_pong(None)


    def start_messaging(self, zmq_context: 'zmq.Context'=None):
        if self._messaging_started:
            s = (' {} messaging already started! Use `update_messaging` '
                'instead of start')

            s = s.format(self._service_name)

            self._logger.warn(s)
            return

        create_n_conn = self._socket_factory.create_n_connect
        to_address = self._socket_factory.to_address

        # Instantiate all the sockets
        command_address = to_address(self._configuration['command_port'])
        self.command_socket = create_n_conn(zmq.DEALER,
                                            command_address,
                                            socket_name='command socket')

        control_address = to_address(self._configuration['control_port'])
        self.control_socket = create_n_conn(zmq.DEALER,
                                            control_address,
                                            socket_name='control socket')

        request_address = to_address(self._configuration['request_port'])
        self.request_socket = create_n_conn(zmq.ROUTER,
                                            request_address,
                                            socket_name='request socket')

        publish_address = to_address(self._configuration['chatter_publish_port'])
        self.publish_socket = create_n_conn(zmq.PUB,
                                            publish_address,
                                            socket_name='publish socket')

        iter_ = self._socket_factory.iterate_multiple_addresses
        subscription_address = iter_(self._configuration['chatter_subscription_port'])
        multiple_conn = self._socket_factory.multiple_create_n_connect
        self.subscription_socket = multiple_conn(zmq.SUB,
                                                 subscription_address,
                                                 socket_name='subscription socket')

        # register the control socket to the poller
        self.poller.register(self.control_socket, zmq.POLLIN)
        self.poller.register(self.command_socket, zmq.POLLIN)
        self.poller.register(self.request_socket, zmq.POLLIN)
        self.poller.register(self.subscription_socket, zmq.POLLIN)

        if self._socket_filter is not None:
            self.set_socket_filter(self._socket_filter)
        else:
            self.subscription_socket.setsockopt(zmq.SUBSCRIBE, b'')

        self._messaging_started = True

    def set_socket_filter(self, filter_):
        self._socket_filter = filter_

        if self.subscription_socket:
            self.subscription_socket.setsockopt_string(zmq.SUBSCRIBE, filter_)

    def send_chatter(self, target: str='', **msg):
        frame = create_vex_message(target, self._service_name, 'MSG', **msg)
        self.publish_socket.send_multipart(frame)

    def send_command(self, command: str, *args, **kwargs):
        """
        For request bot to perform some action
        """
        command = command.encode('ascii')
        args = pickle.dumps(args)
        kwargs = pickle.dumps(kwargs)
        self.command_socket.send_multipart((b'', command, args, kwargs))

    def send_control(self, control, **kwargs):
        """
        Time critical commands
        """
        # frame = create_vex_message()
        self.command_socket.send_multipart(frame)

    def send_response(self, status, target='', **kwargs):
        """
        frame = create_vex_message(target,
                                   self._service_name,
                                   'STATUS',
                                   status=status,
                                   **kwargs)

        self.request_socket.send_multipart(frame)
        """
        raise RuntimeError('Not implemented')

    def send_ping(self):
        self.command_socket.send_multipart((b'', b'PING'))

    def _disconnect_socket(self, socket, socket_name, address=None):
        if address is None:
            address = self._address[socket_name]

        # can have `None` for value
        if not address:
            return
        try:
            socket.disconnect(address)
        except zmq.error.ZMQError:
            pass

        self._address[socket_name] = None
