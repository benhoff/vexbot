import os
import sys
import asyncio
from asyncio.streams import StreamWriter, FlowControlMixin

from adapters import Adapter
from message import Message

class Shell(Adapter):
    def __init__(self, bot=None):
        super(Shell, self).__init__()
        self._writer = None
        self._reader = None
        self.bot = bot
        self.messages = []

    def _stdio(self, loop=None):
        if loop is None:
            loop = asyncio.get_event_loop()
            self._reader = asyncio.StreamReader()
            reader_protocol = asyncio.StreamReaderProtocol(self._reader)
            writer_transport, writer_protocol = yield from loop.connect_write_pipe(FlowControlMixin, os.fdopen(0, 'wb'))
            self._writer = StreamWriter(writer_transport, writer_protocol, None, loop)
            yield from loop.connect_read_pipe(lambda: reader_protocol, sys.stdin)

    def send(self, message):
        if self._writer is not None:
            self._writer.write(message)
    
    @asyncio.coroutine
    def run(self, loop=None):
        # Initialzies the plugin
        yield from self._stdio()
        while True:
            self._writer.write('{}> '.format(self.bot.name).encode('utf-8'))
            line = yield from self._reader.readline()
            if line == b'':
                pass
            else:
                str_input = line.decode('ascii')
                inputs = str_input.split(self.bot.name)
                for input in inputs:
                    command, string_arg = input.split(' ', 1)
                    msg = Message(command, string_arg)
                    self.bot.message(msg)

if __name__ == '__main__':
    shell = Shell()
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(shell.run(loop))
    finally:
        loop.close()
