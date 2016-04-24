import os
import re
import sys
import types
import logging
import asyncio
from os import path

import yaml
import pluginmanager
from vexparser.classification_parser import ClassifyParser

from vexbot.middleware import Middleware
from vexbot.messaging import Messaging
from vexbot.plugin_wrapper import PluginWrapper


class Robot:
    def __init__(self, config_path=None, bot_name="vex"):
        self.name = bot_name
        self._logger = logging.getLogger(__name__)
        self.messaging = Messaging()

        data_file = path.join(path.dirname(__file__), 'example.yaml')
        with open(data_file) as f:
            data = yaml.load(f)

        self.parser = ClassifyParser(data)

        # adapters are inputs into the bot. Like a mic or shell input
        adapter_manager = pluginmanager.PluginInterface()
        adapter_manager.set_entry_points('vexbot.adapters')
        plugins = adapter_manager.collect_entry_point_plugins()
        pub_address = 'tcp://127.0.0.1:5555'
        self.messager.subscribe_to_address(pub_address)
        # self.messaging.thread.start()
        self.adapters = []

        self.listeners = []
        self.commands = []

        # self.receive_middleware = Middleware(bot=self)
        # self.listener_middleware = Middleware(bot=self)
        self.catch_all = None

    def run(self):
        while True:
            frame = self.messaging.sub_socket.recv_multipart()
            # I.E. Shell adapter
            source = frame[0]
            msg = frame[1]
            result = self.parser.parse(msg)
            print(result)

    def listener_middleware(self, middleware):
        self.listener_middleware.stack.append(middleware)

    def _process_listeners(self, response, done=None):
        for listener in self.listeners:
            result, done = listener.call(response.message.command,
                                         response.message.argument,
                                         done)

            #self.listener_middleware.execute(result, done=done)

            if isinstance(done, bool) and done:
                # TODO: pass back to the appropriate adapter?
                print(result)
                return
            elif isinstance(done, types.FunctionType) and result:
                done()
                print(result)
                return

        if self.catch_all is not None:
            self.catch_all()

    def recieve(self, message, callback=None):
        response = Response(self, message)
        done = self.receive_middleware.execute(response,
                                               self._process_listeners,
                                               callback)

        if isinstance(done, bool) and done:
            return
        self._process_listeners(response, done)

    """
    def run(self, event_loop=None):
        loop = asyncio.get_event_loop()
        for adapter in self.adapters:
            asyncio.async(adapter.run())
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            loop.close()
        sys.exit()
    """

    def shutdown(self):
        pass

if __name__ == '__main__':
    robot = Robot()
