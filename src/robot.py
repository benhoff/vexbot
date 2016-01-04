import os
import re
import sys
import types
import logging
import asyncio

import yaml

from listener import Listener
from response import Response
import adapters
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
        # FIXME: nominal api
        #self.plugin_manager.grab_plugins()
        self.listener_middleware = Middleware(bot=self)
        self.catch_all = None

    def listen(self, matcher_function, callback):
        self.listeners.append(Listener(self, matcher_function, callback))

    def hear(self, regex, callback):
        match_function = regex.match
        self.listeners.append(Listener(self, match_function, callback))

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

    def run(self, event_loop=None):
        loop = asyncio.get_event_loop()
        for adapter in self.adapters:
            asyncio.async(adapter.run())
        try:
            loop.run_forever()
        finally:
            loop.close()

    def shutdown(self):
        pass
