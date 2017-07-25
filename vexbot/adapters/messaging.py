import zmq
import logging

from vexbot import _get_default_port_config

from vexmessage import create_vex_message, decode_vex_message


class ZmqMessaging:
    def __init__(self, service_name: str, socket_filter: str, **kwargs):
        """
        `socket_filter`: is used for the chatter pub/sub sockets. Can be set to
                         all using an empty string `str()`

        `kwargs`:
            protocol:   'tcp'
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
            if self._heartbeat in socks:
                try:
                    msg = self._heartbeat.recv_multipart(zmq.NOBLOCK)
                    if msg[1] == b'PING':
                        pong_response = [msg[0],
                                         self._service_name.encode('ascii'),
                                         b'PONG']

                        self._heartbeat.send_multipart(pong_response)
                    elif msg[1] == b'PONG':
                        self._handle_pong(msg[0].decode('ascii'))
                except zmq.error.Again:
                    pass
            if self.sub_socket in socks:
                try:
                    msg = self.sub_socket.recv_multipart(zmq.NOBLOCK)
                    try:
                        yield decode_vex_message(msg)
                    except Exception:
                        pass
                except zmq.error.Again:
                    pass

    def start_messaging(self, zmq_context: 'zmq.Context'=None):
        if self._messaging_started:
            s = ' {} messaging already started! Use `update_messaging` '
                'instead of start'.format(self._service_name)

            self._logger.warn(s)
            return

        context = zmq_context or zmq.Context()

        # Instantiate all the sockets
        self.command_socket = context.socket(zmq.DEALER)
        self.control_socket = context.socket(zmq.DEALER)
        self.request_socket = context.socket(zmq.ROUTER)
        self.publish_socket = context.socket(zmq.PUB)
        self.subscription_socket = context.socket(zmq.SUB)

        # Get the control socket address
        control_address = self._configuration['control_port']
        control_address = self._address_helper(control_address)

        # connect the control socket to it's address
        self.control_socket.connect(control_address)
        # register the control socket to the poller
        self.poller.register(self.control_socket, zmq.POLLIN)

        # Get the command socket address
        command_address = self._configuration['command_port']
        command_address = self._address_helper(command_address)

        # connect the command socket to it's address
        self.command_socket.connect(command_address)
        # register the command socket to the poller
        self.poller.register(self.command_socket, zmq.POLLIN)

        # Get the request socket address
        request_address = self._configuration['request_port']
        request_address = self._address_helper(request_address)

        # connect the request socket to it's address
        self.request_socket.connect(request_address)
        # register the request socket
        self.poller.register(self.request_socket, zmq.POLLIN)

        # Get the chatter publish socket address
        chatter_pub_address = self._configuration['chatter_publish_port']
        chatter_pub_address = self._address_helper(chatter_publish_address)

        # connect the publish socket to it's address
        self.publish_socket.connect(chatter_pub_address)

        # Get the chatter subscirption socket addresses
        chatter_sub_address = self._configuration['chatter_subscription_port']
        # if they are a single instance (instead of an iterable) convert them
        # to a tuple
        if isinstance(chatter_sub_address, (int, str)):
            chatter_sub_address = (chatter_sub_address,)

        for addr in chatter_sub_address:
            # Get the subscription address
            addr = self._address_helper(addr)
            # connect it to the socket
            self.subscription_socket.connect(addr)
        # register the subscription socket to the poller
        self.poller.register(self.subscription_socket, zmq.POLLIN)

        # TODO: add in the socket filter logic where applicable
        """
        if self._socket_filter is not None:
            self.set_socket_filter(self._socket_filter)
            self._heartbeat.setsockopt_string(zmq.IDENTITY,
                                              self._socket_filter)
        """

        self._messaging_started = True

    # TODO: fix the logic in this method call. Uses old socket names (i.e.
    # `self.pub_socket`
    """
    def update_messaging(self,
                         pub_address=None,
                         sub_addresses=None,
                         heartbeat_address=None,
                         disconnect_old_addr=True):

        # if not self._messaging_started:
        #    self.start_messaging()

        if pub_address:
            if disconnect_old_addr:
                self.disconnect_pub_socket(self._address['pub'])

            self.pub_socket.connect(pub_address)
            self._address['pub'] = pub_address

        if sub_addresses:
            if disconnect_old_addr:
                self.disconnect_sub_socket(self._address['sub'])
            for s in sub_addresses:
                self.sub_socket.connect(s)
            self._address['sub'] = sub_addresses

        if heartbeat_address:
            if disconnect_old_addr:
                self.disconnect_heartbeat_socket(self._address['heart'])
            self._heartbeat.connect(heartbeat_address)
            self._address['heart'] = heartbeat_address
    """

    def set_socket_filter(self, filter_):
        self._socket_filter = filter_

        if self.subscription_socket:
            self.subscription_socket.setsockopt_string(zmq.SUBSCRIBE, filter_)

    def send_message(self, target='', **msg):
        frame = create_vex_message(target, self._service_name, 'MSG', **msg)
        self.pub_socket.send_multipart(frame)

    def send_status(self, status, target='', **kwargs):
        frame = create_vex_message(target,
                                   self._service_name,
                                   'STATUS',
                                   status=status,
                                   **kwargs)

        self.pub_socket.send_multipart(frame)

    def send_command(self, target='', **command):
        frame = create_vex_message(target,
                                   self._service_name,
                                   'CMD',
                                   **command)

        self.pub_socket.send_multipart(frame)

    def send_ping(self):
        # TODO: Think about putting a service here?
        # TODO: nowait?
        self._heartbeat.send(b'PING', zmq.NOBLOCK)

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

    def _address_helper(self, port):
        """
        returns a zmq address
        """
        # check to see if user passed in a string
        # if they did, they want to use that instead
        if isinstance(port, str) and len(port) > 6:
            return port

        zmq_address = '{}://{}:{}'
        return zmq_address.format(self.protocol,
                                  self.ip_address,
                                  port)
