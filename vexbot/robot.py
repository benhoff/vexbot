import sys as _sys
import logging as _logging

from vexbot.messaging import Messaging as _Messaging
from vexbot.scheduler import Scheduler as _Scheduler
from vexbot.observers import BotObserver as _BotObserver

try:
    from vexbot.subprocess_manager import SubprocessManager
except ImportError as e:
    SubprocessManager = False
    _subprocess_manager_error = e


class Robot:
    def __init__(self,
                 messaging: _Messaging=None,
                 command_observer: _BotObserver=None,
                 subprocess_manager=None):

        self.messaging = messaging
        self.scheduler = _Scheduler(messaging)
        log_name = __name__ if __name__ != '__main__' else 'vexbot.robot'
        self._logger = _logging.getLogger(log_name)
        if subprocess_manager is None and SubprocessManager:
            subprocess_manager = SubprocessManager()
        else:
            err = ('If you would like to use the subporcess manager, please '
                   'run `pip install -e .[process_manager]` from the '
                   'directory')

            self._logger.warn(err)

        self.subprocess_manager = subprocess_manager

        if command_observer is None:
            command_observer = _BotObserver(messaging,
                                            self.subprocess_manager)

        self.command_observer = command_observer
        self.scheduler.command.subscribe(self.command_observer)

    def run(self):
        if self.messaging is None:
            e = ' No `messaging` provided to `Robot` on initialization'
            self._logger.error(e)
            _sys.exit(1)

        self.messaging.start()
        # NOTE: blocking call
        self.scheduler.run()
