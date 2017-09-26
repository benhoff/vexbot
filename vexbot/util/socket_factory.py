import sys as _sys
import zmq as _zmq

class SocketFactory:
    """
    Abstracts out the socket creation, specifically the issues with transforming ports into zmq addresses. 
    Also sets up some default protocol and ip_address handeling.
    For example, if everything is being run locally on one machine, and the default is to use
    the ip_address `127.0.0.1` and the transport protocol `tcp` means tcp communication
    """
    def __init__(self,
                 ip_address: str,
                 protocol: str='tcp',
                 context: 'zmq.Context'=None,
                 logger: 'logging.Logger'=None):

        self.ip_address = ip_address
        self.protocol = protocol
        self.context = context or _zmq.Context.instance()
        self.logger = logger

    def create_n_connect(self,
                         socket_type,
                         address: str,
                         bind=False,
                         on_error='log',
                         socket_name=''):
        """
        Creates and connects or binds the sockets
        on_error: 
            'log': will log error
            'exit': will exit the program
        socket_name:
            used for troubleshooting/logging
        """
        socket = self.context.socket(socket_type)
        if bind:
            try:
                socket.bind(address)
            except _zmq.error.ZMQError:
                self._handle_error(on_error, address, socket_name)
                socket = None
        else: # connect the socket
            socket.connect(address)

        return socket

    def multiple_create_n_connect(self,
                                  socket_type,
                                  addresses: tuple,
                                  bind=False,
                                  on_error='log',
                                  socket_name=''):

        socket = self.context.socket(socket_type)
        for address in addresses:
            if bind:
                try:
                    socket.bind(address)
                except _zmq.error.ZMQError:
                    self._handle_error(on_error, address, socket_name)
                    socket = None
            else: # connect the socket
                socket.connect(address)

        return socket

    def to_address(self, port: str):
        """
        transforms the ports into addresses.
        Will fall through if the port looks like an address
        """
        # check to see if user passed in a string
        # if they did, they want to use that instead
        if isinstance(port, str) and len(port) > 6:
            return port

        zmq_address = '{}://{}:{}'
        return zmq_address.format(self.protocol,
                                  self.ip_address,
                                  port)

    def iterate_multiple_addresses(self, ports: (str, list, tuple)):
        """
        transforms an iterable, or the expectation of an iterable
        into zmq addresses
        """
        if isinstance(ports, (str, int)):
            # TODO: verify this works.
            addresses = tuple(ports,)

        result = []
        for port in ports:
            result.append(self.to_address(port))

        return result

    def _handle_error(self, how_to: str, ip_address: str, socket_name: str):
        if socket_name == '':
            socket_name = 'unknown type'

        if how_to == 'exit':
            self._handle_bind_error_by_exit(ip_address, socket_name)
        else:
            self._handle_bind_error_by_log(ip_address, socket_name)

    def _handle_bind_error_by_log(self, ip_address: str, socket_name: str):
        if self.logger is None:
            return
        s = 'Address bind attempt fail. Address tried: {}'
        s = s.format(ip_address)
        self.logger.error(s)
        self.logger.error('socket type: {}'.format(socket_type))

    def _handle_bind_error_by_exit(self, ip_address: str, socket_type: str):
        if self.logger is not None:
            s = 'Address bind attempt fail. Address tried: {}'
            s = s.format(ip_address)
            self.logger.error(s)
            self.logger.error('socket type: {}'.format(socket_type))

        sys.exit(1)
