import re
import asyncio

class Socket(object):
    def __init__(self, bot=None, host='localhost', port=6000):
        self.host = host
        self.port = port
        self.connection = None
        self.reader = None
        self.writer = None
        self.is_activated = False
    
    def message(self, message):
        argument = message.argument if message.argument else ''
        message = ''.join([message.command.pattern, ' ', argument, '\n'])
        self.writer.write(message.encode('utf-8'))

    @asyncio.coroutine
    def activate(self):
        self.reader, self.writer = yield from asyncio.open_connection(self.host, self.port)
        print('socket activated!')
        self.is_activated = True
    
    @asyncio.coroutine
    def run(self):
        if not self.is_activated:
            return
