import asyncio

class Socket(object):
    def __init__(self, bot=None, host='localhost', port=6000):
        self.bot = bot
        self.host = host
        self.port = port
        self.server = None

        self.port_occupied = False 
        self.is_activated = False
        self.readers = []
        self.writers = []
        self.adapter = None

    @asyncio.coroutine
    def call(self, response):
        print(response)
        if self.adapter:
            try:
                adapter_response = yield from self.adapter.message(response.command)
            except Exception as e:
                print(e)

    def _client_connected(self, reader, writer):
        print('client connected!')
        self.readers.append(reader)
        self.writers.append(writer)


    @asyncio.coroutine
    def activate(self):
        if self.is_activated:
            return

        # Try to create a server listener
        try:
            self.server = yield from asyncio.start_server(self._client_connected, self.host, self.port)
            print('server created!')
            self.is_activated = True

        # If address and port is already in use, 
        # create an adapter for address and port!
        except OSError:
            print('server not created!')
            self.adapter = self.bot.add_socket_helper(self.host, self.port)
            self.is_activated = True 

    @asyncio.coroutine
    def run(self):
        print(self.is_activated, 'run')
        if not self.is_activated:
            return
        while True:
            print(self.readers)
            for reader in self.readers:
                command = yield from reader.read(8192)
                print(command)
