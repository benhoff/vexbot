import sys
import os
import atexit
import signal
import logging
import asyncio
import argparse
import tempfile
import pkg_resources
from time import sleep

import sqlalchemy as _alchy

import zmq
from zmq import ZMQError
from vexmessage import decode_vex_message

from vexbot.command_managers import AdapterCommandManager
from vexbot.adapters.messaging import ZmqMessaging # flake8: noqa
from vexbot.sql_helper import Base

_GOOGLE_API_INSTALLED = True

try:
    pkg_resources.get_distribution('google-api-python-client')
except pkg_resources.DistributionNotFound:
    _GOOGLE_API_INSTALLED = False

if _GOOGLE_API_INSTALLED:
    import httplib2

    from apiclient.discovery import build
    from oauth2client.client import flow_from_clientsecrets
    from oauth2client.file import Storage
    from oauth2client.tools import run_flow, argparser


async def _run(messaging, live_chat_messages, live_chat_id, ):
    command_manager = AdapterCommandManager(messaging)
    frame = None
    while True:
        try:
            frame = messaging.sub_socket.recv_multipart(zmq.NOBLOCK)
        except zmq.error.ZMQError:
            pass
        if frame:
            message = decode_vex_message(frame)
            if message.type == 'CMD':
                command_manager.parse_commands(message)
            elif message.type == 'RSP':
                message = message.contents.get('response')
                body={'snippet':{'type': 'textmessageEvent',
                                 'liveChatId': live_chat_id,
                                 'textMessageDetails': {'messageText': message}}}

                live_chat_messages.insert(part='snippet',
                                          body=body).execute()

            frame = None

        await asyncio.sleep(1)


def _handle_close(messaging, event_loop):
    def inner(*args):
        _send_disconnect(messaging)()
        for task in asyncio.Task.all_tasks():
            task.cancel()
        event_loop.stop()
    return inner


def _send_disconnect(messaging):
    def inner():
        messaging.send_status('DISCONNECTED')
    return inner


class YoutubeSettings(Base):
    __tablename__ = 'youtube_settings'
    id = _alchy.Column(_alchy.Integer, primary_key=True)
    publish_address = _alchy.Column(_alchy.String(length=100))
    subscribe_address = _alchy.Column(_alchy.String(length=100))
    client_secret_filepath = _alchy.Column(_alchy.String(length=4096))


def main(client_secret_filepath, publish_address, subscribe_address):
    if not _GOOGLE_API_INSTALLED:
        logging.error('`google-api-python-client` required to use youtube. Install using `pip install google-api-python-client')
        return

    # TODO: Determine if this try/except pattern has become outdated
    # with new `connect` methods being called rather than the old bind
    try:
        messaging = ZmqMessaging('youtube',
                                 publish_address,
                                 subscribe_address,
                                 'youtube')

        messaging.start_messaging()
    except ZMQError:
        return

    # signal.signal(signal.SIGINT, handle_close)
    # signal.signal(signal.SIGTERM, handle_close)
    # handle_close = _handle_close(messaging)

    scope = ['https://www.googleapis.com/auth/youtube',
             'https://www.googleapis.com/auth/youtube.force-ssl',
             'https://www.googleapis.com/auth/youtube.readonly']

    youtube_api = _youtube_authentication(client_secret_filepath, scope)
    parts = 'snippet'
    livestream_response = youtube_api.liveBroadcasts().list(mine=True,
                                                            part=parts,
                                                            maxResults=1).execute()


    live_chat_id = livestream_response.get('items')[0]['snippet']['liveChatId']

    livechat_response = youtube_api.liveChatMessages().list(liveChatId=live_chat_id, part='snippet').execute()

    next_token = livechat_response.get('nextPageToken')
    polling_interval = livechat_response.get('pollingIntervalMillis')
    polling_interval = _convert_to_seconds(polling_interval)
    messaging.send_status('CONNECTED')

    event_loop = asyncio.get_event_loop()
    asyncio.ensure_future(_recv_loop(messaging,
                                     youtube_api,
                                     live_chat_id,
                                     next_token,
                                     polling_interval))

    asyncio.ensure_future(_run(messaging,
                               youtube_api.liveChatMessages(),
                               live_chat_id))

    atexit.register(_send_disconnect(messaging))
    event_loop.run_forever()


    messaging.send_status('DISCONNECTED')


async def _recv_loop(messaging,
                     youtube_api,
                     live_chat_id,
                     next_token,
                     polling_interval):

    while True:
        await asyncio.sleep(polling_interval)
        part = 'snippet, authorDetails'
        livechat_response = youtube_api.liveChatMessages().list(liveChatId=live_chat_id, part=part, pageToken=next_token).execute()

        next_token = livechat_response.get('nextPageToken')
        polling_interval = livechat_response.get('pollingIntervalMillis')
        polling_interval = _convert_to_seconds(polling_interval)

        for live_chat_message in livechat_response.get('items'):
            snippet = live_chat_message['snippet']
            if not bool(snippet['hasDisplayContent']):
                continue
            message = snippet['displayMessage']
            author = live_chat_message['authorDetails']['displayName']
            messaging.send_message(author=author, message=message)

def _convert_to_seconds(milliseconds: str):
    return float(milliseconds)/1000.0


def _get_kwargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('--client_secret_filepath')
    parser.add_argument('--publish_address')
    parser.add_argument('--subscribe_address')
    args = parser.parse_args()
    kwargs = vars(args)

    return kwargs


_YOUTUBE_API_SERVICE_NAME = 'youtube'
_YOUTUBE_API_VERSION = 'v3'
_READ_ONLY = "https://www.googleapis.com/auth/youtube.readonly"


def _youtube_authentication(client_filepath, youtube_scope=_READ_ONLY):
    missing_client_message = "You need to populate the client_secrets.json!"
    flow = flow_from_clientsecrets(client_filepath,
                                   scope=youtube_scope,
                                   message=missing_client_message)

    dir = os.path.abspath(__file__)
    filepath = "{}-oauth2.json".format(dir)
    # remove old oauth files to be safe
    if os.path.isfile(filepath):
        os.remove(filepath)

    storage = Storage(filepath)
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage, argparser.parse_args())
        return build(_YOUTUBE_API_SERVICE_NAME,
                     _YOUTUBE_API_VERSION,
                     http=credentials.authorize(httplib2.Http()))


def _get_youtube_link(client_secrets_filepath):
    youtube_api = youtube_authentication(client_secrets_filepath)
    parts = 'id, snippet, status'
    livestream_requests = youtube_api.liveBroadcasts().list(mine=True,
                                                            part=parts,
                                                            maxResults=5)

    while livestream_requests:
        response = livestream_requests.execute()
        # TODO: add better parsing here
        youtube_id = response.get('items', [])[0]['id']
        return 'http://youtube.com/watch?v={}'.format(youtube_id)


if __name__ == '__main__':
    kwargs = _get_kwargs()
    # OAuth2 lib has some argparse functionality that conflicts with ours
    # delete ours for ease of programming
    for _ in range(6):
        del sys.argv[1]
    main(**kwargs)
