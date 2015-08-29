import sys
import asyncio
if sys.platform == 'win32'
    from asyncio.windows_utils import Popen, PIPE
else:
    from subprocess import Popen, PIPE

from adapter import Adapter

class Shell(Adapter):
    def __init__(self):
        super(Shell, self).__init__()

    @asyncio.coroutine
    def run(self, loop=None):
        # TODO: Figure out how to get the shell that's already running
        # instead of making a new one
        code = r'''if 1:
                       import os
                       def writeall(fd, buf):
                           while buf:
                               n = os.write(fd, buf)
                               buf = buf[n:]
                       while True:
                           s = os.read(0, 1024)
                           if not s:
                               break
                           s = s.decode('ascii')
                           s = repr(eval(s)) + '\n'
                           s = s.encode('ascii')
                           writeall(1, s)
                       '''

        commands = iter([b"1+1\n",
                         b"2**16\n",
                         b"1/3\n",
                         b"'x'*50",
                         b"1/0\n"])

        p = Popen([sys.executable, '-c', code],
                  stdin=PIPE, stdout=PIPE, stderr=PIPE)

        stdin = yield from self._connect_write_pipe(p.stdin)
        stdout, stdout_transport = yield from self._connect_read_pipe(p.stdout)
        stderr, stderr_transport = yield from self._connect_read_pipe(p.stderr)

        name = {stdout: 'OUT', stderr: 'ERR'}
        registered = {asyncio.Task(stderr.readline()): stderr,
                      asyncio.Task(stdout.readline()): stdout}

        while registered:
            cmd = next(commands, None)
            if cmd is None:
                stdin.close()
            else:
                print('>>>', cmd.decode('ascii').rstrip())
                stdin.write(cmd)

            timeout = None
            while registered:
                done, pending = yield from asyncio.wait(
                        registered, timeout=timeout,
                        return_when=asyncio.FIRST_COMPLETED)
                if not done:
                    break
                for f in done:
                    stream = registered.pop(f)
                    res = f.result()
                    print(name[stream], res.decode('ascii').rstrip())
                    if res != b'':
                        registered[asyncio.Task(stream.readline())] = stream

                timeout = 0.0

        stdout_transport.close()
        stderr_transport.close()

    @asyncio.coroutine
    def _connect_read_pipe(self, file):
        loop = asyncio.get_event_loop()
        stream_reader = asyncio.StreamReader(loop=loop)
        def factory():
            return asyncio.StreamReaderProtocol(stream_reader)
        transport, _= yield from loop.connect_read_pipe(factory, file)
        return stream_reader, transport
    
    @asyncio.coroutine
    def _connect_write_pipe(self, file):
        loop = asyncio.get_event_loop()
        transport, _ = yield from loop.connect_write_pipe(asyncio.Protocol, file)
        return transport

if __name__ == '__main__':
    shell = Shell()
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(shell.run(loop))
    finally:
        loop.close()
