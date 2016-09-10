import sys
import atexit
import signal
import asyncio
import argparse
import logging
import pkg_resources

import sqlalchemy as _alchy

import zmq
from zmq import ZMQError
from vexmessage import decode_vex_message

from vexbot.command_managers import AdapterCommandManager
from vexbot.adapters.messaging import ZmqMessaging
from vexbot.sql_helper import Base

_IRC3_INSTALLED = True

try:
    pkg_resources.get_distribution('irc3')
except pkg_resources.DistributionNotFound:
    _IRC3_INSTALLED = False


class IrcSettings(Base):
    __tablename__ = 'irc_settings'
    id = _alchy.Column(_alchy.Integer, primary_key=True)
    service_name = _alchy.Column(_alchy.String(length=50), unique=True)
    password = _alchy.Column(_alchy.String(length=100))
    channel = _alchy.Column(_alchy.String(length=30))
    nick = _alchy.Column(_alchy.String(length=30))
    host = _alchy.Column(_alchy.String(length=50))
    publish_address = _alchy.Column(_alchy.String(length=100))
    subscribe_address = _alchy.Column(_alchy.String(length=100))
    robot_model_id = _alchy.Column(_alchy.Integer,
                                      _alchy.ForeignKey('robot_models.id'))

    robot_model = _alchy.orm.relationship("RobotModel")


if _IRC3_INSTALLED:
    import irc3
    from irc3.plugins.autojoins import AutoJoins

    @irc3.plugin
    class AutoJoinMessage(AutoJoins):
        requires = ['irc3.plugins.core', ]

        def __init__(self, bot):
            super().__init__(bot)

        def connection_lost(self):
            self.bot.messaging.send_status('DISCONNECTED')
            super(AutoJoinMessage, self).connection_lost()

        def join(self, channel=None):
            super(AutoJoinMessage, self).join(channel)
            self.bot.messaging.send_status('CONNECTED')

        @irc3.event(irc3.rfc.KICK)
        def on_kick(self, mask, channel, target, **kwargs):
            self.bot.messaging.send_status('DISCONNECTED')
            super().on_kick(mask, channel, target, **kwargs)

        @irc3.event("^:\S+ 47[1234567] \S+ (?P<channel>\S+).*")
        def on_err_join(self, channel, **kwargs):
            self.bot.messaging.send_status('DISCONNECTED')
            super().on_err_join(channel, **kwargs)

    @irc3.plugin
    class EchoToMessage(object):
        requires = ['irc3.plugins.core',
                    'irc3.plugins.command']

        def __init__(self, bot):
            self.bot = bot

        @irc3.event(irc3.rfc.PRIVMSG)
        def message(self, mask, event, target, data):
            nick = mask.nick
            message = data
            self.bot.messaging.send_message(author=nick,
                                            message=str(message),
                                            channel=target)


def create_irc_bot(nick,
                   password,
                   host=None,
                   port=6667,
                   realname=None,
                   channel=None):

    config = dict(ssl=False,
                  includes=['irc3.plugins.core',
                            'irc3.plugins.command',
                            'irc3.plugins.human',
                            __name__])

    if realname is None:
        realname = nick
    if channel is None:
        channel = nick

    config['nick'] = nick
    config['password'] = password
    config['host'] = host
    config['port'] = port
    config['username'] = realname
    config['autojoins'] = channel
    config['level'] = 30

    bot = irc3.IrcBot.from_config(config)

    return bot


async def _check_subscription(bot):
    while True:
        await asyncio.sleep(1)
        msg = None
        try:
            msg = bot.messaging.sub_socket.recv_multipart(zmq.NOBLOCK)
        except zmq.error.Again:
            pass
        if msg:
            msg = decode_vex_message(msg)
            if msg.type == 'CMD':
                bot.command_parser.parse_commands(msg)
            elif msg.type == 'RSP':
                channel = msg.contents.get('channel')
                message = msg.contents.get('response')
                bot.privmsg(channel, message)
                bot.messaging.send_message(author=bot.nick,
                                           message=message,
                                           channel=channel)


def _default(*args, **kwargs):
    pass


def _call_func_with_arg(func, arg):
    def inner(*args):
        return func(arg)
    return inner


def _send_disconnected(messaging):
    def inner():
        messaging.send_status('DISCONNECTED')
    return inner


def _handle_close(messaging, event_loop):
    def inner(signum=None, frame=None):
        _send_disconnected(messaging)()
        event_loop.stop()
        for task in asyncio.Task.all_tasks():
            task.cancel()
    return inner


def main(nick,
         password,
         host,
         channel,
         publish_address,
         subscribe_address,
         service_name):

    if not _IRC3_INSTALLED:
        logging.error('irc requires `irc3` to be installed. Please install '
                      'using `pip install irc3`')

    irc_client = create_irc_bot(nick,
                                password,
                                host,
                                channel=channel)

    try:
        messaging = ZmqMessaging(service_name,
                                 publish_address,
                                 subscribe_address,
                                 socket_filter=service_name)

        messaging.start_messaging()
    except ZMQError:
        return
    # Duck type messaging onto irc_client, FTW
    irc_client.messaging = messaging
    command_parser = AdapterCommandManager(messaging)
    irc_client.command_parser = command_parser

    """
    command_parser.register_command('server config', _default)
    command_parser.register_command('ip', _default)
    command_parser.register_command('join', _default)
    command_parser.register_command('kick', _default)
    command_parser.register_command('part', _default)
    command_parser.register_command('invite', _default)
    command_parser.register_command('topic', _default)
    command_parser.register_command('away', _default)
    """

    irc_client.create_connection()
    irc_client.add_signal_handlers()
    event_loop = asyncio.get_event_loop()
    asyncio.ensure_future(_check_subscription(irc_client))
    atexit.register(_send_disconnected(messaging))

    handle_close = _handle_close(messaging, event_loop)
    signal.signal(signal.SIGINT, handle_close)
    signal.signal(signal.SIGTERM, handle_close)
    try:
        event_loop.run_forever()
    except KeyboardInterrupt:
        pass
    event_loop.close()
    sys.exit()


def _get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--nick')
    parser.add_argument('--password')
    parser.add_argument('--host')
    parser.add_argument('--channel')
    parser.add_argument('--publish_address')
    parser.add_argument('--subscribe_address')
    parser.add_argument('--service_name')

    return parser.parse_args()


if __name__ == '__main__':

    kwargs = vars(_get_args())
    main(**kwargs)
