import asyncio
import argparse
import logging
import pkg_resources

from zmq import ZMQError

from vexbot.adapters.messaging import ZmqMessaging
from vexbot.subprocess_manager import SubprocessManager

_IRC3_INSTALLED = True



class IrcInterface:
    def __init__(self, **kwargs):
        self.irc_bot = kwawrgs.get('bot')
        self.messaging = None
        self.command_parser = None


def create_irc_bot(nick,
                   password,
                   host=None,
                   port=6667,
                   realname=None,
                   channel=None,
                   **kwargs):

    if realname is None:
        realname = nick
    if channel is None:
        channel = nick

    config = {'ssl': False,
              'includes': ['irc3.plugins.core',
                           'irc3.plugins.command',
                           'irc3.plugins.human',
                           __name__],
              'nick': nick,
              'password': password,
              'host': host,
              'port': port,
              'username': realname,
              'autojoins': channel,
              'level': 30}

    bot = irc3.IrcBot.from_config(config)

    return bot

else: #irc3 not installed
    def create_irc_bot(*args, **kwargs):
        pass


def _handle_close(messaging, event_loop):
    def inner(signum=None, frame=None):
        event_loop.stop()
        for task in asyncio.Task.all_tasks():
            task.cancel()
    return inner
