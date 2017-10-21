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
                 service_name,
                 bot_nick='EchoBot',
                 **kwargs):

        # Initialize the parent class
        super().__init__(jid, password)
        self.messaging = Messaging(service_name,
                                   run_control_loop=True)

        self.room = room
        self.nick = bot_nick
        # self.log = logging.getLogger(__file__)
        # self['feature_mechanisms'].unencrypted_plain = True

        # One-shot helper method used to register all the plugins
        self._register_plugin_helper()

        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler("groupchat_message", self.muc_message)
        self._thread = Thread(target=self.messaging.start, daemon=True)
        self._thread.start()

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

    def session_start(self, event):
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
