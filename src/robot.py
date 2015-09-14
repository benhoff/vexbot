import os
import sys
import logging
import asyncio

import yaml
import simpleyapsy
import plugins

from listener import Listener
from response import Response
from adapters import Shell
from adapters import Socket as SocketAdapter
from middleware import Middleware

class Bot(object):
    def __init__(self, config_path=None, bot_name="vex"):
        self.name = bot_name
        self._logger = logging.getLogger(__name__)

        # adapters are inputs into the bot. Like a mic or shell input
        self.adapters = []
        self.adapters.append(Shell(bot=self))

        self.listeners = []
        self.commands = []

        self.receive_middleware = Middleware(bot=self)
        self.plugin_manager = simpleyapsy.PluginManager()
        self.plugin_manager.add_dirs(plugins.__path__[0])
        # FIXME: nominal api
        self.plugin_manager.grab_plugins()
        self.listener_middleware = Middleware(bot=self)

    def listen(self, matcher_function, callback):
        pass

    def hear(self, regex, callback):
        # FIXME
        self.listeners.append(Listener(self, regex, callback))

    def catch_all(self, callback):
        pass

    def listener_middleware(self, middleware):
        self.listener_middleware.stack.append(middleware)

    def _process_listeners(self, response, done=None):
        for listener in self.listeners:
            result, done = listener.call(response.message.command, 
                                         response.message.argument, 
                                         done)
            
            #self.listener_middleware.execute(result, done=done)

            print(result, done)
    
            if isinstance(done, bool) and done:
                # TODO: pass back to the appropriate adapter?
                print(result)
                return

    def recieve(self, message, callback=None):
        response = Response(self, message)
        done = self.receive_middleware.execute(response,
                                               self._process_listeners,
                                               callback)

        if isinstance(done, bool) and done:
            return
        self._process_listeners(response, done)

    def add_socket_helper(self, host, port):
        socket = SocketAdapter(self, host, port)
        asyncio.async(socket.activate())
        self.adapters.append(socket)
        return socket
    
    def run(self, event_loop=None):
        loop = asyncio.get_event_loop()
        # TODO: Need to block slightly on a module
        asyncio.async(self.receive_middleware.activate())
        for adapter in self.adapters:
            asyncio.async(adapter.run())
        try:
            loop.run_forever()
        finally:
            loop.close()

    def shutdown(self):
        pass
