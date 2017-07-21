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

        if command_manager is None:
            command_manager = _BotCommandManager(robot=self)

        self.command_manager = command_manager

        self.adapter_interface.start_profile('default')

        log_name = __name__ if __name__ != '__main__' else 'vexbot.robot'
        self._logger = _logging.getLogger(log_name)

    def run(self):
        # TODO: error log if self.messaging is None, otherwise this will throw
        # an error on None type
        self.messaging.start()
        for msg in self.messaging.run():
            # TODO: add in authentication
            if msg.type == 'CMD':
                self.command_manager.parse_commands(msg)
