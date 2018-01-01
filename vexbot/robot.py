import sys as _sys
import logging as _logging

from vexbot import _get_default_port_config
from vexbot.messaging import Messaging as _Messaging
from vexbot.adapters.shell.observers import LogObserver
from vexbot.command_observer import CommandObserver as _CommandObserver
# NOTE: Intents currently not finished/working
# from vexbot.intents import BotIntents

# NOTE: import will fail if `pydbus` isn't installed. Downgrade functionallity
# rather than error out.
try:
    from vexbot.subprocess_manager import SubprocessManager
except ImportError:
    SubprocessManager = False
    _logging.exception('Import Error for subprocess manager!')

# NOTE: import will fail if `nlp` isn't installed. Downgrade functionallity
# rather than error out.
try:
    from vexbot.language import Language
except ImportError:
    Language = False
    _logging.exception('Import Error for language!')


class Robot:
    def __init__(self,
                 bot_name: str='vexbot',
                 connection: dict=None,
                 subprocess_manager: SubprocessManager=None,
                 cache_filepath: str=None):
        """
        This is the server/main robot for vexbot.

        Args:
            bot_name (str): the name used by the bot and for identification
                programatic identification purposes. Cannot contain whitespaces
            connection (dict): the Zmq address information used for messaging.
                See documentation for format. Defaults to the following:
                {protocol: 'tcp',
                 address: '*',
                 chatter_publish_port: 4000,
                 chatter_subscription_port: [4001,],
                 command_port: 4002,
                 request_port: 4003,
                 control_port: 4005}
            subprocess_manger: See 'vexbot._abstract_process_manager.py'
                for class definition if not using the provided dbus
                implementation.
        """

        if connection is None:
            connection = _get_default_port_config()

        # Create messaging for bot
        self.messaging = _Messaging(bot_name, **connection)
        # Get a name for the logging, either the filename or 'vexbot.robot'
        log_name = __name__ if __name__ != '__main__' else 'vexbot.robot'
        self._logger = _logging.getLogger(log_name)

        # Check to see if we imported SubprocessManager successfully
        # initialize an instance if we did and an instance wasn't passed in.
        if subprocess_manager is None and SubprocessManager:
            subprocess_manager = SubprocessManager()
        elif subprocess_manager is None:
            err = ('If you would like to use the subporcess manager, please '
                   'run `pip install -e .[process_manager]` from the '
                   'directory')

            self._logger.warn(err)

        self.subprocess_manager = subprocess_manager

        # NOTE: probably need some kind of config here
        if Language:
            self.language = Language()
        else:
            err = ('If you would like to use natural language processing,'
                   ' please run `pip install -e.[nlp]` from the directory')
            self._logger.warn(err)
            self.language = False

        # self.intents = BotIntents()
        # Create the command observer, which is the main command processing
        # point
        self.command_observer = _CommandObserver(self,
                                                 self.messaging,
                                                 self.subprocess_manager,
                                                 self.language,
                                                 cache_filepath)

        # subscribe the command observer to the command subject
        self.messaging.command.subscribe(self.command_observer)
        # subscribe a log observer to chatter feed. Will pass logs on.
        self.messaging.chatter.subscribe(LogObserver(pass_through=True))

    def run(self):
        """
        Run the bot. Blocking call.
        """
        # Bot needs messaging to run. Fail fast.
        if self.messaging is None:
            e = ' No `messaging` provided to `Robot` on initialization'
            self._logger.error(e)
            _sys.exit(1)

        self._logger.info(' Start Messaging')

        # Catch KeyboardInterrupt
        try:
            # TODO: Put small primer on the logic flow for bot here
            # NOTE: blocking call. Starts the bot.
            self.messaging.start()
        except KeyboardInterrupt:
            # NOTE: Sometimes it appears that the bot will hang on
            # KeyboardInterrupt. This seems to resolve that issue.
            self.messaging.loop.stop()
