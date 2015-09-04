import multiprocessing
import asyncio
from adapters import Socket as SocketAdapter

class Socket(object):
    def __init__(self, bot=None, 
                 address=('localhost', 6000),
                 family='AF_INET', authkey=None):
        
        self.bot = bot
        self.address = address
        self.family = family
        self.authkey = authkey
        self.listener = None
    
    @asyncio.coroutine
    def run(self):
        # Try to create a listener
        try:
            self.listener = multiprocessing.connection.Listener(self.address,
                                                                self.family,
                                                                authkey=self.authkey)
        # If address and port is already in use, 
        # create an adapter for address and port!
        except OSError:
            adapter = SocketAdapter(self.bot, self.address,
                                    self.family, self.authkey)

            self.bot.adapters.append(adapter)

        """
        with self.listener.accept() as conn:
            print('connection accepted from', self.listener.last_accepted)
            conn.send_bytes(b'hello!')
        """
