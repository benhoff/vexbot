import asyncio
from message import Message

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

    def call(self, response):
        if self.adapter:
            try:
                adapter_response = self.adapter.message(response)
            except Exception as e:
                print(e)

    @asyncio.coroutine
    def _handle_client(self, reader, writer):
        print('client connected!')
        self.readers.append(reader)
        self.writers.append(writer)
        while True:
            line = yield from reader.readline()
            if not line:
                print('broke')
                break
            line = line.decode('utf-8').rstrip()
            try:
                command, string_arg = line.split(' ', 1)
            except ValueError:
                command = line
                string_arg = None
            msg = Message(command, string_arg)
            print(msg)
            self.bot.recieve(msg)

    @asyncio.coroutine
    def activate(self):
        if self.is_activated:
            return

        # Try to create a server listener
        try:
            self.server = yield from asyncio.start_server(self._handle_client, self.host, self.port)
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
        while True:
            if not self.is_activated:
                yield from asyncio.sleep(1)
            else:
                yield from asyncio.sleep(1)
