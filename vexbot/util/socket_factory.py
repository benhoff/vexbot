import sys as _sys
import zmq as _zmq

class SocketFactory:
    """
    Abstracts out the socket creation, specifically the issues with transforming ports into zmq addresses. 
    Also sets up some default protocol and ip_address handeling.
    For example, if everything is being run locally on one machine, and the default is to use
    the ip_address `127.0.0.1` and the transport protocol `ipc` means interprocess communication
    """
    def __init__(self, ip_address: str, protocol: str='ip', context: 'zmq.Context'):
        self.ip_address = ip_address
        self.protocol = protocol
        self.context = context or _zmq.Context.instance()

    def create_socket(self, type_, port: int, on_error='log'):
        pass

    def _handle_multiple_ports(self, *args, **kwargs):
        if isinstance(addresses, (str, int)):
            # TODO: verify this works.
            addresses = tuple(addresses,)

        # Can subscribe to multiple addresses
        for addr in addresses:
            ip_address = self._address_helper(addr)

            # TODO: verify that this shouldn't be like a connect
            try:
                self.subscription_socket.bind(ip_address)
            except _zmq.error.ZMQError:
                self._handle_bind_error_by_log(ip_address, 'subscription')

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

    def _handle_bind_error_by_log(self, ip_address, socket_type):
        s = 'Address bind attempt fail. Address tried: {}'
        s = s.format(ip_address)
        self._logger.error(s)
        self._logger.error('socket type: {}'.format(socket_type))

    def _handle_bind_error_by_exit(self, ip_address, socket_type):
        s = 'Address bind attempt fail. Address tried: {}'
        s = s.format(ip_address)
        self._logger.error(s)
        self._logger.error('socket type: {}'.format(socket_type))
        sys.exit(1)
