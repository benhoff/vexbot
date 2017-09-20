import sys as _sys
import logging as _logging

import zmq

from vexmessage import decode_vex_message

from vexbot.messaging import Messaging as _Messaging
from vexbot.command_managers import BotCommands as _BotCommands
from vexbot.subprocess_manager import SubprocessManager
from vexbot.scheduler import Scheduler as _Scheduler


class Robot:
    def __init__(self,
                 messaging: _Messaging=None,
                 command_manager: _BotCommands=None,
                 subprocess_manager=None):

        self.messaging = messaging
        self.scheduler = _Scheduler(messaging)
        self.subprocess_manager = subprocess_manager or SubprocessManager()
        self.command_manager = command_manager or _BotCommands(messaging,
                                                               self.subprocess_manager)

        self.scheduler.command.subscribe(self.command_manager)


        log_name = __name__ if __name__ != '__main__' else 'vexbot.robot'
        self._logger = _logging.getLogger(log_name)

    def run(self):
        if self.messaging is None:
            e = ' No `messaging` provided to `Robot` on initialization'
            self._logger.error(e)
            _sys.exit(1)

        self.messaging.start()
        # NOTE: blocking call
        self.scheduler.run()
