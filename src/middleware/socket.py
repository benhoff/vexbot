import types
import asyncio
from message import Message
from user import User

class Socket(object):
    # TODO: break into two separate classes and make this a manager class
    def __init__(self, bot=None, host='localhost', port=6000):
        self.bot = bot
        self.host = host
        self.port = port
        self.server = None

        self.port_occupied = False 
        self.is_activated = False
        self.readers = []
        self.writers = []
        self.socket = None

    def call(self, bot, response, next=None, done=None):
        # Need to do three things
        # if this is a client of a server, try to ask server first!
        #   if server does not respond, continue
        #   if server does respond, stop messaging?

        # if this is the server, continue 
        if self.socket:
            try:
                self.socket.message(response)
                # NOTE: nominal interface, not working
                # TODO: add in timeout
                #result = yield from self.socket.readline()
                result = None
                if result:
                    original_adapter = response.message.adapter
                    original_adapter.reply(result)
                    if isinstance(done, types.FunctionType):
                        done()
                    done = True
                    return next, done
                else:
                    return next, done

            except Exception as e:
                print(e)
                return next, done
        else:
            # NOTE: If there isn't a socket, assume server and return
            return next, done

    @asyncio.coroutine
    def _handle_client(self, reader, writer):
        #print('client connected!')
        self.readers.append(reader)
        self.writers.append(writer)
        while True:
            line = yield from reader.readline()
            if not line:
                print('broke')
                break

            # NOTE: passing in the writer to the user obj?
            line = line.decode('utf-8').rstrip()
            print(line)
            try:
                command, string_arg = line.split(' ', 1)
            except ValueError:
                command = line
                string_arg = None
            user = User('1', room='socket', writer=writer)
            msg = Message(self, user, command, string_arg)
            self.bot.recieve(msg)

    @asyncio.coroutine
    def activate(self):
        if self.is_activated:
            return

        # Try to create a server listener
        try:
            self.server = yield from asyncio.start_server(self._handle_client, self.host, self.port)
            #print('server created!')
            self.is_activated = True

        # If address and port is already in use, 
        # create an adapter for address and port!
        except OSError:
            #print('server not created!')
            self.socket = self.bot.add_socket_helper(self.host, self.port)
            self.is_activated = True 

    @asyncio.coroutine
    def run(self):
        while True:
            if not self.is_activated:
                yield from self.activate()
            else:
                yield from asyncio.sleep(1)
