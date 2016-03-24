import os
import sys
import asyncio
import argparse

from asyncio.streams import StreamWriter, FlowControlMixin

import zmq

from vexbot.adapters.adapter import Adapter
from vexbot.user import User
from vexbot.message import Message

class Shell(Adapter):
    def __init__(self,
                 context=None,
                 prompt_name='vexbot',
                 pub_address=''):

        super().__init__()
        self._writer = None
        self._reader = None
        context = context or zmq.Context()
        self.pub_socket = context.socket(zmq.PUB)
        self.pub_socket.bind(pub_address)
        self.pub_address = pub_address
        self.prompt_name = prompt_name
        self.is_activated = False

    async def activate(self):
        loop = asyncio.get_event_loop()
        self._reader = asyncio.StreamReader()
        reader_protocol = asyncio.StreamReaderProtocol(self._reader)
        writer_transport, writer_protocol = await loop.connect_write_pipe(FlowControlMixin, os.fdopen(0, 'wb'))
        self._writer = StreamWriter(writer_transport, writer_protocol, None, loop)
        await loop.connect_read_pipe(lambda: reader_protocol, sys.stdin)
        self.is_activated = True

    def send(self, message):
        if self._writer is not None:
            self._writer.write(message)

    def reply(self, message):
        raise Exception("not implemented")

    def receive(self, message):
        super().receive
        raise Exception("not impelemented")

    async def run(self, loop=None):
        if not self.is_activated:
            await self.activate()

        while True:
            self._writer.write('{}: '.format(self.prompt_name).encode('utf-8'))
            line = await self._reader.readline()
            if line == b'':
                pass
            else:
                user = User('1', room='shell')
                str_input = line.decode('ascii')
                inputs = str_input.split(self.prompt_name)
                for input in inputs:
                    try:
                        command, string_arg = input.split(' ', 1)
                        string_arg.rstrip()
                    except ValueError:
                        command = input.rstrip()
                        string_arg = None
                    # msg = Message(user, command, string_arg)
                    self.pub_socket.send(command.encode('ascii'))


def _get_kwargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pub_address')
    parser.add_argument('--prompt_name')

    args = parser.parse_args()
    return vars(args)


def main():
    kwargs = _get_kwargs()
    shell = Shell(**kwargs)
    asyncio.ensure_future(shell.run())

    loop = asyncio.get_event_loop()

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()

if __name__ == '__main__':
    main()
