import sys as _sys
import zmq as _zmq
from os import path

from zmq.auth.thread import ThreadAuthenticator
from zmq.auth.ioloop import IOLoopAuthenticator

from vexbot.util.get_certificate_filepath import (get_certificate_filepath,
                                                  get_vexbot_certificate_filepath,
                                                  get_client_certificate_filepath)

class SocketFactory:
    """
    Abstracts out the socket creation, specifically the issues with
    transforming ports into zmq addresses.
    Also sets up some default protocol and address handeling.
    For example, if everything is being run locally on one machine, and the
    default is to bind all addresses `*` and the transport protocol
    `tcp` means tcp communication
    """
    def __init__(self,
                 address: str,
                 protocol: str='tcp',
                 context: 'zmq.Context'=None,
                 logger: 'logging.Logger'=None,
                 loop=None,
                 auth_whitelist: list='127.0.0.1'):

        self.address = address
        self.protocol = protocol
        self.context = context or _zmq.Context.instance()
        self.logger = logger
        self._server_certs = (None, None)

        if loop is None:
            self.auth = ThreadAuthenticator(self.context)
        else:
            self.auth = IOLoopAuthenticator(self.context, io_loop=loop)

        # allow all local host
        self.logger.debug('Auth whitelist %s', auth_whitelist)
        self.auth.allow(auth_whitelist)
        self._base_filepath = get_certificate_filepath()
        public_key_location = path.join(self._base_filepath, 'public_keys')
        self.auth.configure_curve(domain='*', location=public_key_location)
        self.auth.start()

    def _set_server_certs(self, any_=True):
        secret_filepath, secret = get_vexbot_certificate_filepath()
        if not secret and not any_:
            # FIXME: This err sucks. Also, build in no Auth case
            err = 'Could not find the vexbot certificates. Did you generate them'
            raise FileNotFoundError(err)
        self._server_certs = _zmq.auth.load_certificate(secret_filepath)

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
        self.logger.debug('create and connect: %s %s %s',
                          socket_type, socket_name, address)

        socket = self.context.socket(socket_type)
        if not any(self._server_certs):
            self._set_server_certs(bind)
        if bind:
            if self._server_certs[1] is None:
                # FIXME: This error sucks
                raise FileNotFoundError('Server Secret File Not Found!')
            public, private = self._server_certs
        else:
            # NOTE: This raises a `FileNotFoundError` currently if not found
            secret_filepath = get_client_certificate_filepath()
            public, private = _zmq.auth.load_certificate(secret_filepath)

        socket.curve_secretkey = private
        socket.curve_publickey = public

        if bind:
            socket.curve_server = True
            try:
                socket.bind(address)
            except _zmq.error.ZMQError:
                self._handle_error(on_error, address, socket_name)
                socket = None
        else:  # connect the socket
            socket.curve_serverkey = self._server_certs[0]
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
            else:  # connect the socket
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
                                  self.address,
                                  port)

    def iterate_multiple_addresses(self, ports: (str, list, tuple)):
        """
        transforms an iterable, or the expectation of an iterable
        into zmq addresses
        """
        if isinstance(ports, (str, int)):
            # TODO: verify this works.
            ports = tuple(ports,)

        result = []
        for port in ports:
            result.append(self.to_address(port))

        return result

    def _handle_error(self, how_to: str, address: str, socket_name: str):
        if socket_name == '':
            socket_name = 'unknown type'

        if how_to == 'exit':
            self._handle_bind_error_by_exit(address, socket_name)
        else:
            self._handle_bind_error_by_log(address, socket_name)

    def _handle_bind_error_by_log(self, address: str, socket_name: str):
        if self.logger is None:
            return
        s = 'Address bind attempt fail. Address tried: {}'
        s = s.format(address)
        self.logger.error(s)
        self.logger.error('socket type: {}'.format(socket_name))

    def _handle_bind_error_by_exit(self, address: str, socket_type: str):
        if self.logger is not None:
            s = 'Address bind attempt fail. Alredy in use? Address tried: {}'
            s = s.format(address)
            self.logger.error(s)
            self.logger.error('socket type: {}'.format(socket_type))

        _sys.exit(1)
