import zmq
import pickle

import logging as _logging
from vexmessage import ReqMessage

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

    def _handle_command_raw(self, message):
        address = []
        for part in message:
            if part == b'':
                break
            address.append(part)
       
        # NOTE: there should be a blank string between
        # the address piece and the message content, which is why
        # we don't have to correct the `address_length` by subtracking
        # one to get in terms of a list length
        address_length = len(address) + 1
        message = message[address_length:]
        command = message.pop(0).decode('ascii')
        if command == 'PING':
            address.append(b'PONG')
            self.messaging.command_socket.send_multipart(address)
            return
        args = message.pop(0)
        args = pickle.loads(args)
        try:
            kwargs = message.pop(0)
        except IndexError:
            kwargs = args
            args = []
        else:
            kwargs = pickle.loads(kwargs)

        message = ReqMessage(command, address, args=args, kwargs=kwargs)

        cs = self.command_manager.process_command(message)
        print(cs)

    def run(self):
        # TODO: error log if self.messaging is None, otherwise this will throw
        # an error on None type
        self.messaging.start()
        self.running = True
        while self.running:
            socks = dict(self.messaging._poller.poll(timeout=500))
            if self.messaging.control_socket in socks:
                # msg = self.messaging._get_message_helper(self.control_socket)
                msg = self.messaging.control_socket.recv_multipart()
                # FIXME: Implement

            if self.messaging.publish_socket in socks:
                try:
                    msg = self.messaging.publish_socket.recv_multipart(zmq.NOBLOCK)
                    print(msg, 'publish')
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
                msg = self.messaging.command_socket.recv_multipart()
                self._handle_command_raw(msg)
                # msg = self.messaging._get_message_helper(self.messaging.command_socket)

            if self.messaging.request_socket in socks:
                # msg = self.messaging._get_message_helper(self.request_socket)
                msg = self.messaging.request_socket.recv_multipart()
                print(msg, 'request')
                
