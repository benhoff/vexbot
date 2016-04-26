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
from vexparser.callback_manager import CallbackManager

from vexbot.adapter_starter import AdapterStart
from vexbot.middleware import Middleware
from vexbot.messaging import Messaging
from vexbot.plugin_wrapper import PluginWrapper


def _return_closure(print_statement):
    def return_func():
        return print_statement
    return return_func


class Robot:
    def __init__(self, config_path=None, bot_name="vex"):
        self.name = bot_name
        self._logger = logging.getLogger(__name__)
        self.messaging = Messaging()

        data_file = path.join(path.dirname(__file__), 'example.yaml')
        with open(data_file) as f:
            data = yaml.load(f)

        classifier_data = []
        self.adapter_starter = AdapterStart()

        self.callback_manager = CallbackManager()

        for intent, intent_data in data['adapters'].items():
            intent_data_for_classifier = [(d, intent)
                                          for d
                                          in intent_data['training_data']]

            classifier_data.extend(intent_data_for_classifier)
            c = self.adapter_starter.track_adapter(intent, intent_data)
            self.callback_manager.associate_key_with_callback(intent, c)

        self.parser = ClassifyParser(classifier_data)
        self.parser.add_callback_manager(self.callback_manager)

        # adapters are inputs into the bot. Like a mic or shell input
        adapter_manager = pluginmanager.PluginInterface()
        adapter_manager.set_entry_points('vexbot.adapters')
        plugins = adapter_manager.collect_entry_point_plugins()
        pub_address = 'tcp://127.0.0.1:5555'
        self.messaging.subscribe_to_address(pub_address)
        # self.messaging.thread.start()
        self.adapters = []

        self.listeners = []
        self.commands = []

        # self.receive_middleware = Middleware(bot=self)
        # self.listener_middleware = Middleware(bot=self)
        self.catch_all = None

    def run(self):
        while True:
            frame = self.messaging.sub_socket.recv_pyobj()
            # I.E. Shell adapter
            source = frame[0]
            msg = frame[1]
            results = self.parser.parse(msg)

            # check to see if go into a context mode here?
            """
            with self.parser.parse(msg):
                pass
            """

            # Here's an alternative idea
            """
            for callback in self.parser.parse(msg):
                with callback(self.messaging)
            """

            # third idea would be to spin up a subprocess that
            # takes over the receving socket for awhile?

            self.messaging.pub_socket.send_pyobj(results)

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
    robot.run()
