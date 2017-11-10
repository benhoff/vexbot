import sys as _sys
import logging as _logging

from vexbot.language import Language
from vexbot import _get_default_port_config
from vexbot.intents import BotIntents
from vexbot.messaging import Messaging as _Messaging
from vexbot.adapters.shell.observers import LogObserver
from vexbot.observers import CommandObserver as _CommandObserver

try:
    from vexbot.subprocess_manager import SubprocessManager
except ImportError as e:
    SubprocessManager = False
    _subprocess_manager_error = e


class Robot:
    def __init__(self,
                 bot_name: str,
                 connection: dict=None,
                 subprocess_manager=None):

        if connection is None:
            connection = _get_default_port_config()

        self.messaging = _Messaging(bot_name, **connection)
        log_name = __name__ if __name__ != '__main__' else 'vexbot.robot'
        self._logger = _logging.getLogger(log_name)
        if subprocess_manager is None and SubprocessManager:
            subprocess_manager = SubprocessManager()
        else:
            err = ('If you would like to use the subporcess manager, please '
                   'run `pip install -e .[process_manager]` from the '
                   'directory')

            self._logger.warn(err)

        # NOTE: probably need some kind of config here
        self.language = Language()
        self.intents = BotIntents()
        self.subprocess_manager = subprocess_manager
        self.command_observer = _CommandObserver(self,
                                                 self.messaging,
                                                 self.subprocess_manager,
                                                 self.language)

        self.messaging.command.subscribe(self.command_observer)
        self.messaging.chatter.subscribe(LogObserver(pass_through=True))

    def run(self):
        if self.messaging is None:
            e = ' No `messaging` provided to `Robot` on initialization'
            self._logger.error(e)
            _sys.exit(1)

        self._logger.info(' Start Messaging')
        # NOTE: blocking call
        try:
            self.messaging.start()
        except KeyboardInterrupt:
            _sys.exit(0)
