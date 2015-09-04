import multiprocessing
import asyncio

class Socket(object):
    def __init__(self, bot=None, 
                 address=('127.0.0.1', 65432),
                 family='AF_INET', authkey=None):

        self.address = address
        self.family = family
        self.authkey = authkey
        self.connection = None
    
    @asyncio.coroutine
    def run(self):
        # NOTE: want to see the failure for when something occupies
        # that address
        self.connection = multiprocessing.connection.Client(self.address,
                                                            self.family,
                                                            authkey=self.authkey)

        # NOTE: nominal implemenation
        #self.bot.add_middleware()

