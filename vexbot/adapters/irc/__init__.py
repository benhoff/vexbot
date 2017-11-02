import asyncio
import argparse
import logging
import pkg_resources

from threading import Thread
try:
    import irc3
except ImportError:
    irc3 = False

if not irc3:
    raise ImportError('irc3 is not installed. Install irc3 using `pip install '
                      'irc3` on the command line')

from vexbot._logging import LoopPubHandler
from vexbot.adapters.messaging import Messaging as _Messaging
from vexbot.adapters.irc.observer import IrcObserver as _IrcObserver


class IrcInterface:
    def __init__(self,
                 service_name: str,
                 irc_config: dict=None,
                 connection: dict=None,
                 **kwargs):


        if connection is None:
            connection = {}

        self.messaging = _Messaging(service_name, run_control_loop=True, **connection)

        self.root_handler = LoopPubHandler(self.messaging)
        self.root_logger = logging.getLogger()
        self.root_logger.addHandler(self.root_handler)

        self._scheduler_thread = Thread(target=self.messaging.start,
                                        daemon=True)

        self.irc_bot = irc3.IrcBot.from_config(irc_config)
        # Duck type messaging to irc bot. Could also subclass `irc3.IrcBot`,
        # but seems like overkill
        self.irc_bot.messaging = self.messaging
        self.command_parser = _IrcObserver(self.irc_bot, self.messaging, self)
        self.messaging.command.subscribe(self.command_parser)

    def run(self):
        self._scheduler_thread.start()

        self.irc_bot.create_connection()
        self.irc_bot.add_signal_handlers()
        event_loop = asyncio.get_event_loop()

        """
        handle_close = _handle_close(messaging,
                                    event_loop)
        signal.signal(signal.SIGINT, handle_close)
        signal.signal(signal.SIGTERM, handle_close)
        """
        event_loop.run_forever()
        event_loop.close()
