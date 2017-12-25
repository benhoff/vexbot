import argparse
import json
import html
import logging
import pkg_resources
import atexit
from time import sleep
from threading import Thread

from vexmessage import decode_vex_message

from vexbot.adapters.messaging import Messaging 
from vexbot.adapters.socket_io.observer import SocketObserver
try:
    from websocket import WebSocketApp
except ImportError:
    logging.error('Socket IO needs `websocket` installed. Please run `pip '
                  'install websocket-client`')
try:
    import requests
except ImportError as e:
    logging.error('Socket IO needs `requests` installed. Please run `pip '
                  'install requests`')


class WebSocket(WebSocketApp):
    def __init__(self,
                 streamer_name: str,
                 namespace: str,
                 website_url: str,
                 service_name: str,
                 connection: dict=None):

        self.log = logging.getLogger(__name__)
        self.log.setLevel(0)
        if connection is None:
            connection = {}

        self.messaging = Messaging(service_name, run_control_loop=True, **connection)
        self._scheduler_thread = Thread(target=self.messaging.start,
                                        daemon=True)

        self._scheduler_thread.start()
        self.observer = SocketObserver(self, self.messaging)
        self.messaging.command.subscribe(self.observer)

        self._streamer_name = streamer_name
        self.namespace = namespace
        self._website_url = website_url
        self.log.info('Getting Socket IO key!')
        self.key, heartbeat = self._connect_to_server_helper()
        self.log.info('Socket IO key got!')
        # self.command_manager = AdapterCommandManager(self.messaging)

        # alters URL to be more websocket...ie
        self._website_socket = self._website_url.replace('http', 'ws')
        self._website_socket += 'websocket/'
        self.nick = None
        super().__init__(self._website_socket + self.key,
                         on_open=self.on_open,
                         on_close=self.on_close,
                         on_message=self.on_message,
                         on_error=self.on_error)

    def _connect_to_server_helper(self):
        r = requests.post(self._website_url)
        params = r.text

        # unused variables are connection_timeout and supported_formats
        key, heartbeat_timeout, _, _ = params.split(':')
        heartbeat_timeout = int(heartbeat_timeout)
        return key, heartbeat_timeout

    def on_open(self, *args):
        logging.info('Websocket open!')

    def on_close(self, *args):
        logging.info('Websocket closed :(')

    def on_message(self, *args):
        message = args[1].split(':', 3)
        key = int(message[0])
        # namespace = message[2]

        if len(message) >= 4:
            data = message[3]
        else:
            data = ''
        if key == 1 and args[1] == '1::':
            self.send_packet_helper(1)
        elif key == 1 and args[1] == '1::{}'.format(self.namespace):
            self.send_packet_helper(5, data={'name': 'initialize'})
            data = {'name': 'join',
                    'args': ['{}'.format(self._streamer_name)]}

            self.send_packet_helper(5, data=data)
            self.log.info('Connected to channel with socket io!')
            # self.messaging.send_status('CONNECTED')
        elif key == 2:
            self.send_packet_helper(2)
        elif key == 5:
            data = json.loads(data, )
            if data['name'] == 'message':
                message = data['args'][0]
                sender = html.unescape(message['sender'])
                if sender == self.nick:
                    return
                message = html.unescape(message['text'])
                self.messaging.send_chatter(author=sender, message=message)
            elif data['name'] == 'join':
                self.nick = data['args'][1]

    def on_error(self, *args):
        logging.error(args[1])

    def disconnect(self):
        callback = ''
        data = ''
        # '1::namespace'
        self.send(':'.join([str(self.TYPE_KEYS['DISCONNECT']),
                           callback, self.namespace, data]))

    def send_packet_helper(self,
                           type_key,
                           data=None):

        if data is None:
            data = ''
        else:
            data = json.dumps(data)

        # NOTE: callbacks currently not implemented
        callback = ''
        message = ':'.join([str(type_key), callback, self.namespace, data])
        self.send(message)
