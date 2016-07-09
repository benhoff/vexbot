import argparse
import json
import requests
import html
import logging
import signal
import atexit
from time import sleep
from threading import Thread

import websocket
from zmq import ZMQError
from vexmessage import decode_vex_message

from vexbot.command_managers import AdapterCommandManager
from vexbot.adapters.messaging import ZmqMessaging


class ReadOnlyWebSocket(websocket.WebSocketApp):
    # NOTE: chat_signal defined in `__init__`

    def __init__(self,
                 streamer_name,
                 namespace,
                 website_url,
                 publish_address,
                 subscribe_address,
                 service_name):

        self.log = logging.getLogger(__name__)
        self.log.setLevel(0)
        self.messaging = ZmqMessaging(service_name,
                                      publish_address,
                                      subscribe_address,
                                      'socket_io')

        self.messaging.start_messaging()
        self._streamer_name = streamer_name
        self.namespace = namespace
        self._website_url = website_url
        self.log.info('Getting Socket IO key!')
        self.key, heartbeat = self._connect_to_server_helper()
        self.log.info('Socket IO key got!')
        self.command_manager = AdapterCommandManager(self.messaging)
        self._thread = Thread(target=self.handle_subscription)
        self._thread.start()

        # alters URL to be more websocket...ie
        self._website_socket = self._website_url.replace('http', 'ws')
        self._website_socket += 'websocket/'
        super().__init__(self._website_socket + self.key,
                         on_open=self.on_open,
                         on_close=self.on_close,
                         on_message=self.on_message,
                         on_error=self.on_error)

    def handle_subscription(self):
        while True:
            frame = self.messaging.sub_socket.recv_multipart()
            message = decode_vex_message(frame)
            if message.type == 'CMD':
                self.command_manager.parse_commands(message)

    def repeat_run_forever(self):
        while True:
            try:
                self.run_forever()
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.log.info('Socket IO errors: {}'.format(e))
            self.messaging.send_status('DISCONNECTED')
            sleep(3)
            key, _ = self._connect_to_server_helper()
            self.url = self._website_socket + key

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
            self.messaging.send_status('CONNECTED')
        elif key == 2:
            self.send_packet_helper(2)
        elif key == 5:
            data = json.loads(data, )
            if data['name'] == 'message':
                message = data['args'][0]
                sender = html.unescape(message['sender'])
                message = html.unescape(message['text'])
                self.messaging.send_message(author=sender, message=message)

    def on_error(self, *args):
        print(args[1])

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


def _get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--streamer_name')
    parser.add_argument('--namespace')
    parser.add_argument('--website_url')
    parser.add_argument('--service_name')
    parser.add_argument('--publish_address')
    parser.add_argument('--subscribe_address')

    return parser.parse_args()


def _handle_close(messaging):
    def inner(*args):
        messaging.send_status('DISCONNECTED')
    return inner


def _send_disconnect(messaging):
    def inner():
        _handle_close(messaging)()
    return inner


if __name__ == '__main__':

    args = vars(_get_args())
    already_running = False
    try:
        client = ReadOnlyWebSocket(**args)
    except ZMQError:
        already_running = True

    if not already_running:
        messaging = client.messaging
        atexit.register(_send_disconnect(messaging))
        handle_close = _handle_close(messaging)
        signal.signal(signal.SIGINT, handle_close)
        signal.signal(signal.SIGTERM, handle_close)
        client.repeat_run_forever()
