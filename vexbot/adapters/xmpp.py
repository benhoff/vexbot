import sys
import logging
import argparse
# import signal
import atexit
import pkg_resources
from threading import Thread

import zmq
from vexmessage import decode_vex_message

from vexbot.adapters.messaging import Messaging # flake8: noqa

from sleekxmpp import ClientXMPP
from sleekxmpp.exceptions import IqError, IqTimeout


class XMPPBot(ClientXMPP):
    def __init__(self,
                 jid,
                 password,
                 room,
                 publish_address,
                 subscribe_address,
                 service_name,
                 bot_nick='EchoBot',
                 **kwargs):

        # Initialize the parent class

        super().__init__(jid, password)
        self.messaging = Messaging(service_name,
                                   run_control_loop=True)

        self.messaging.start()

        self.room = room
        self.nick = bot_nick
        self.log = logging.getLogger(__file__)

        # One-shot helper method used to register all the plugins
        self._register_plugin_helper()

        self.add_event_handler("session_start", self.start)
        self.add_event_handler("groupchat_message", self.muc_message)
        self._thread = Thread(target=self.messaging.scheduler.loop.start, daemon=True)

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
        self._thread.start()
        self.log.info('starting xmpp')
        self.send_presence()
        self.plugin['xep_0045'].joinMUC(self.room,
                                        self.nick,
                                        wait=True)

        self.get_roster()

    def muc_message(self, msg):
        self.messaging.send_chatter(author=msg['mucnick'],
                                    message=msg['body'],
                                    channel=msg['from'].bare)


def _get_args():
    parser = argparse.ArgumentParser()
    # local/username
    parser.add_argument('--local', help='local arg for string parsing')
    # like a url
    parser.add_argument('--domain', help='domain for xmpp')
    parser.add_argument('--room', help='room or channel to join')
    # special identifier for where you're coming from
    parser.add_argument('--resource', help='resource')
    parser.add_argument('--password', help='password')
    parser.add_argument('--service_name')
    parser.add_argument('--publish_address')
    parser.add_argument('--subscribe_address')
    # nick can be different than your local
    parser.add_argument('--bot_nick')

    return parser.parse_args()


def main():
    args = _get_args()
    jid = '{}@{}/{}'.format(args.local, args.domain, args.resource)
    kwargs = vars(args)
    already_running = False

    xmpp_bot = XMPPBot(jid, **kwargs)

    while True:
        xmpp_bot.connect()
        try:
            xmpp_bot.process(block=True)
        finally:
            xmpp_bot.disconnect()

if __name__ == '__main__':
    main()
