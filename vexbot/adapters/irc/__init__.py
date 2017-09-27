import asyncio
import argparse
import logging
import pkg_resources

from threading import Thread

import irc3

from vexbot.adapters.messaging import Messaging as _Messaging
from vexbot.adapters.irc.observer import IrcObserver as _IrcObserver
from vexbot.adapters.scheduler import Scheduler as _Scheduler


class IrcInterface:
    def __init__(self,
                 service_name: str,
                 messaging: _Messaging=None,
                 command_parser=None,
                 irc_config: dict=None,
                 **kwargs):

        # FIXME: Should be passing in some of the kwargs here
        self.messaging = messaging or _Messaging(service_name)


        self.command_parser = command_parser or _IrcObserver(self.messaging)

        self._messaging_scheduler = _Scheduler(self.messaging)
        self._scheduler_thread = Thread(target=self._messaging_scheduler.run, daemon=True)

        self.irc_bot = irc3.IrcBot.from_config(irc_config)
        # Duck type messaging to irc bot. Could also subclass `irc3.IrcBot`,
        # but seems like overkill
        self.irc_bot.messaging = self.messaging

    def run(self):
        self.irc_bot.messaging.start_messaging()
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


def _handle_close(messaging, event_loop):
    def inner(signum=None, frame=None):
        event_loop.stop()
        for task in asyncio.Task.all_tasks():
            task.cancel()
    return inner
