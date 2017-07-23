import logging as _logging

from vexbot.messaging import Messaging as _Messaging
from vexbot.command_managers import BotCommandManager as _BotCommandManager
from vexbot.adapter_interface import AdapterInterface as _AdapterInterface


class Robot:
    def __init__(self,
                 messaging: _Messaging=None,
                 adapter_interface: _AdapterInterface=None,
                 command_manager: _BotCommandManager=None):

        self.messaging = messaging
        self.adapter_interface = adapter_interface
        self.running = False

        if command_manager is None:
            command_manager = _BotCommandManager(robot=self)

        self.command_manager = command_manager

        self.adapter_interface.start_profile('default')

        log_name = __name__ if __name__ != '__main__' else 'vexbot.robot'
        self._logger = _logging.getLogger(log_name)


    def _handle_command(self, command):
        self.command_manager.parse_commands(command)

    def _handle_raw_chatter(self, chatter):
        pass

    def _handle_request(self, request):
        pass

    def run(self):
        # TODO: error log if self.messaging is None, otherwise this will throw
        # an error on None type
        self.messaging.start()
        self.running = True
        while self.running:
            socks = dict(self.messaging._poller.poll(timeout=500))
            if self.messaging.control_socket in socks:
                msg = self.messaging._get_message_helper(self.control_socket)
                if msg is not None:
                    pass

            if self.messaging.publish_socket in socks:
                try:
                    msg = self.messaging.publish_socket.recv_multipart(zmq.NOBLOCK)
                    self.messaging.subscription_socket.send_multipart(msg)
                except zmq.error.Again:
                    pass

            if self.messaging.subscription_socket in socks:
                try:
                    msg = self.messaging.subscription_socket.recv_multipart(zmq.NOBLOCK)
                    self.messaging.publish_socket.send_multipart(msg)
                    self._handle_raw_chatter(msg)
                except zmq.error.Again:
                    pass

            if self.messaging.command_socket in socks:
                msg = self.message._get_message_helper(self.command_socket)
                if msg:
                    self._handle_command(msg)

            if self.messaging.request_socket in socks:
                msg = self.messaging._get_message_helper(self.request_socket)
                if msg:
                    self._handle_request(msg)
