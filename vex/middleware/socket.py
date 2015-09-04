import multiprocessing
import asyncio

class Socket(object):
    def __init__(self, bot=None, 
                 address=('localhost', 6000),
                 family='AF_INET', authkey=None):
        
        self.bot = bot
        self.address = address
        self.family = family
        self.authkey = authkey
        self.listener = None

        self.port_occupied = False 
        self.is_activated = False

    def activate(self, callback=None, *args, **kwargs):
        if self.is_activated:
            return

        # Try to create a listener
        try:
            self.listener = multiprocessing.connection.Listener(self.address,
                                                                self.family,
                                                                authkey=self.authkey)

            print('server created!')
            self.is_activated = True
        # If address and port is already in use, 
        # create an adapter for address and port!
        except OSError:
            print('server not created!')
            self.port_occupied = True
            self.is_activated = False
            if callback is not None:
                callback(self, *args, **kwargs)
                # FIXME: currently this method is not a coroutine
                # due to issues with passing in args. When this is fixed
                # the below line needs to be deleted
                self.is_activated = True

    
    @asyncio.coroutine
    def run(self):
        if not self.is_activated:
            return

        # FIXME: currently this method is not a coroutine
        # due to issues with passing in args. When this is fixed
        # the below line needs to be deleted
        if self.listener is not None:
            with self.listener.accept() as conn:
                print('connection accepted from', self.listener.last_accepted)
                conn.send_bytes(b'hello!')
