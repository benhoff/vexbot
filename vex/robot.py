import os
import sys
import logging
import asyncio

import yaml
from yapsy.PluginManager import PluginManager

import tts, stt
from conversation import Conversation
from adapters import Shell
from adapters import Socket as SocketAdapter
from middleware import Middleware
# FIXME
from middleware import Socket as SocketMiddleware

class Bot(object):
    def __init__(self, config_path=None, bot_name="vex"):
        self.name = bot_name
        # create logger
        self._logger = logging.getLogger(__name__)
        # adapters are inputs into the bot. Like a mic or shell input
        self.adapters = []
        self.adapters.append(Shell(bot=self))

        self._listeners = []
        self._register_plugins()
        self.commands = []
        self.receive_middleware = Middleware(bot=self)

        self.receive_middleware.stack.append(SocketMiddleware(bot=self))
        self.listener_middleware = Middleware(bot=self)

    def _register_plugins(self):
        # FIXME: Something is messing up in here
        self._plugin_manager = PluginManager()
        plugin_path = os.path.dirname(os.path.realpath(__file__))
        plugin_path = os.path.join(plugin_path, 'plugins')
        self._plugin_manager.setPluginPlaces([plugin_path])
        for plugin_info in self._plugin_manager.getAllPlugins():
            self._plugin_manager.activatePluginByName(plugin_info.name)
            plugin_info.plugin_object.set_bot(self)
            self._listeners.append(plugin_info.plugin_object)
        self._plugin_manager.collectPlugins()

    def hear(self, regex, option, callback):
        pass

    def listener_middleware(self, middleware):
        self.listener_middleware.stack.append(middleware)

    def process_listeners(self, response):
        for listener in self._listeners:
            result = listener.call(message.command, message.argument)
            if result is not None:
                print(result)
            # TODO: Return the result to the correct adapter

    def recieve(self, message):
        self.receive_middleware.execute(message, self.process_listeners)

    def add_socket_helper(self, host, port):
        socket = SocketAdapter(self, host, port)
        asyncio.async(socket.activate())
        self.adapters.append(socket)
        return socket
    
    def run(self, event_loop=None):
        loop = asyncio.get_event_loop()
        # TODO: Need to block slightly on a module
        asyncio.async(self.receive_middleware.activate())
        asyncio.async(self.listener_middleware.run())
        asyncio.async(self.receive_middleware.run())
        for adapter in self.adapters:
            asyncio.async(adapter.run())
        try:
            loop.run_forever()
        finally:
            loop.close()
