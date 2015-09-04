import asyncio

class Socket(object):
    def __init__(self, bot=None, host='localhost', port=6000):
        self.bot = bot
        self.host = host
        self.port = port
        self.server = None

        self.port_occupied = False 
        self.is_activated = False

    def _hello_world(self):
        print('socket connected!')

    @asyncio.coroutine
    def activate(self):
        if self.is_activated:
            return

        # Try to create a server listener
        try:
            self.server = yield from asyncio.start_server(self._hello_world, self.host, self.port)
            print('server created!')
            self.is_activated = True

        # If address and port is already in use, 
        # create an adapter for address and port!
        except OSError:
            print('server not created!')
            self.port_occupied = True
            self.bot.add_socket_helper(self.host, self.port)
            self.is_activated = True 

    @asyncio.coroutine
    def run(self):
        if not self.is_activated:
            return
