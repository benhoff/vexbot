import sys
import argparse
import tempfile
from time import sleep

import httplib2

from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow, argparser

from zmq import ZMQError

from vexbot.adapters.communication_messaging import ZmqMessaging # flake8: noqa


def main(client_secret_filepath, socket_address):
    try:
        messaging = ZmqMessaging('youtube', socket_address)
        messaging.set_socket_filter('')
        messaging.start_messaging()
    except ZMQError:
        return

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
    messaging.send_message('CONNECTED')

    while True:
        sleep(polling_interval)
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
            messaging.send_message('MSG', author, message)

    messaging.send_message('DISCONNECTED')

def _convert_to_seconds(milliseconds: str):
    return float(milliseconds)/1000.0


def _get_kwargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('--client_secret_filepath')
    parser.add_argument('--socket_address')
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

    with tempfile.TemporaryDirectory() as tempdir:

        filepath = "{}-oauth2.json".format(tempdir)
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
    for _ in range(4):
        del sys.argv[1]
    main(**kwargs)
