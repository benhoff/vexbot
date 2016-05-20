import logging
import argparse
from sleekxmpp import ClientXMPP
from sleekxmpp.exceptions import IqError, IqTimeout
from time import sleep

import zmq

from vexbot.adapters.communication_messaging import ZmqMessaging # flake8: noqa


class ReadOnlyXMPPBot(ClientXMPP):
    def __init__(self,
                 jid,
                 password,
                 room,
                 socket_address,
                 service_name,
                 bot_nick='EchoBot',
                 **kwargs):

        # Initialize the parent class
        super().__init__(jid, password)
        self.messaging = ZmqMessaging(service_name, socket_address)
        self.messaging.set_socket_filter('')
        self.messaging.start_messaging()

        self.room = room
        self.nick = bot_nick
        self.log = logging.getLogger(__file__)

        # One-shot helper method used to register all the plugins
        self._register_plugin_helper()

        self.add_event_handler("session_start", self.start)
        self.add_event_handler("groupchat_message", self.muc_message)
        self.add_event_handler('connected', self._connected)
        self.add_event_handler('disconnected', self._disconnected)

    def _disconnected(self, *args):
        self.messaging.send_message('DISCONNECTED')

    def _connected(self, *args):
        self.messaging.send_message('CONNECTED')

    def _register_plugin_helper(self):
        """
        One-shot helper method used to register all the plugins
        """
        # Service Discovery
        self.register_plugin('xep_0030')
        # XMPP Ping
        self.register_plugin('xep_0199')
        # Multiple User Chatroom
        self.register_plugin('xep_0045')

    def start(self, event):
        self.log.info('starting xmpp')
        self.send_presence()
        self.plugin['xep_0045'].joinMUC(self.room,
                                        self.nick,
                                        wait=True)

        self.get_roster()

    def muc_message(self, msg):
        self.messaging.send_message('MSG',
                                    msg['mucnick'],
                                    msg['body'])


def _get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--local', help='local arg for string parsing')
    parser.add_argument('--domain', help='domain for xmpp')
    parser.add_argument('--room', help='room!')
    parser.add_argument('--resource', help='resource')
    parser.add_argument('--password', help='password')
    parser.add_argument('--service_name')
    parser.add_argument('--socket_address')
    parser.add_argument('--bot_nick')

    return parser.parse_args()


def main():
    args = _get_args()
    jid = '{}@{}/{}'.format(args.local, args.domain, args.resource)
    kwargs = vars(args)
    already_running = False

    try:
        xmpp_bot = ReadOnlyXMPPBot(jid, **kwargs)
    except zmq.ZMQError:
        already_running = True

    if not already_running:
        while True:
            try:
                xmpp_bot.connect()
                xmpp_bot.process(block=True)
            except Exception as e:
                xmpp_bot.log.error(e)

if __name__ == '__main__':
    main()
