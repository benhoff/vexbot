import argparse
import json
import requests
import html
import logging
from time import sleep

import websocket

from chatimusmaximus.communication_protocols.communication_messaging import ZmqMessaging # flake8: noqa


class ReadOnlyWebSocket(websocket.WebSocketApp):
    # NOTE: chat_signal defined in `__init__`

    def __init__(self,
                 streamer_name,
                 namespace,
                 website_url,
                 socket_address,
                 service_name):

        self.log = logging.getLogger(__name__)
        self.log.setLevel(0)
        self.messaging = ZmqMessaging(service_name, socket_address)
        self._streamer_name = streamer_name
        self.namespace = namespace
        self._website_url = website_url
        self.log.info('Getting Socket IO key!')
        self.key, heartbeat = self._connect_to_server_helper()
        self.log.info('Socket IO key got!')

        # alters URL to be more websocket...ie
        self._website_socket = self._website_url.replace('http', 'ws')
        self._website_socket += 'websocket/'
        super().__init__(self._website_socket + self.key,
                         on_open=self.on_open,
                         on_close=self.on_close,
                         on_message=self.on_message,
                         on_error=self.on_error)

    def repeat_run_forever(self):
        while True:
            try:
                self.run_forever()
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.log.info('Socket IO errors: {}'.format(e))
            sleep(3)
            self.messaging.send_message('DISCONNECTED')
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
            self.messaging.send_message('CONNECTED')
        elif key == 2:
            self.send_packet_helper(2)
        elif key == 5:
            data = json.loads(data, )
            if data['name'] == 'message':
                message = data['args'][0]
                sender = html.unescape(message['sender'])
                message = html.unescape(message['text'])
                self.messaging.send_message('MSG', sender, message)

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
    parser.add_argument('--socket_address')

    return parser.parse_args()


if __name__ == '__main__':

    args = vars(_get_args())
    client = ReadOnlyWebSocket(**args)
    client.repeat_run_forever()
