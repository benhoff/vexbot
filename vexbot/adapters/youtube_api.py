import os
import logging
import asyncio
import argparse
from argparse import Namespace
import tempfile
import pkg_resources
from time import sleep

from vexbot.adapters.messaging import Messaging
from vexbot.adapters.scheduler import Scheduler

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

class Youtube:
    def __init__(self, **kwargs):
        self.messaging = Messaging('youtube')
        scope = ['https://www.googleapis.com/auth/youtube',
                 'https://www.googleapis.com/auth/youtube.force-ssl',
                 'https://www.googleapis.com/auth/youtube.readonly']
        self.api = _youtube_authentication(client_secret_filepath, scope)

    def run(self):
        self.messaging.start()
        parts = 'snippet'
        livestream_response = self.api.liveBroadcasts().list(mine=True,
                                                             part=parts,
                                                             maxResults=1).execute()


        live_chat_id = livestream_response.get('items')[0]['snippet']['liveChatId']

        livechat_response = youtube_api.liveChatMessages().list(liveChatId=live_chat_id, part='snippet').execute()

        next_token = livechat_response.get('nextPageToken')
        polling_interval = livechat_response.get('pollingIntervalMillis')
        polling_interval = _convert_to_seconds(polling_interval)
        while True:
            await asyncio.sleep(polling_interval)
            part = 'snippet, authorDetails'
            livechat_response = self.api.liveChatMessages().list(liveChatId=live_chat_id, part=part, pageToken=next_token).execute()

            next_token = livechat_response.get('nextPageToken')
            polling_interval = livechat_response.get('pollingIntervalMillis')
            polling_interval = _convert_to_seconds(polling_interval)

            for live_chat_message in livechat_response.get('items'):
                snippet = live_chat_message['snippet']
                if not bool(snippet['hasDisplayContent']):
                    continue
                message = snippet['displayMessage']
                author = live_chat_message['authorDetails']['displayName']
                self.messaging.send_chatter(author=author, message=message)


async def _run(messaging, live_chat_messages, live_chat_id, ):
    command_manager = AdapterCommandManager(messaging)
    frame = None
    for message in messaging.run(250):
        if message.type == 'CMD':
            command_manager.parse_commands(message)
        elif message.type == 'RSP':
            message = message.contents.get('response')
            body={'snippet':{'type': 'textmessageEvent',
                             'liveChatId': live_chat_id,
                             'textMessageDetails': {'messageText': message}}}

            live_chat_messages.insert(part='snippet',
                                      body=body).execute()

        await asyncio.sleep(1)



def main(client_secret_filepath, publish_address, subscribe_address):
    if not _GOOGLE_API_INSTALLED:
        logging.error('`google-api-python-client` required to use youtube. Install using `pip install google-api-python-client')
        return


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
_ALL = "https://www.googleapis.com/auth/youtube"


def _youtube_authentication(client_filepath, youtube_scope=_READ_ONLY):
    missing_client_message = "You need to populate the client_secrets.json!"
    flow = flow_from_clientsecrets(client_filepath,
                                   scope=youtube_scope,
                                   message=missing_client_message)

    dir = os.path.abspath(__file__)
    filepath = "{}-oauth2.json".format(dir)
    # TODO: Determine if removing file is needed
    # remove old oauth files to be safe
    if os.path.isfile(filepath):
        os.remove(filepath)

    storage = Storage(filepath)
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        args = Namespace(auth_host_name='localhost',
                         auth_host_port=[8080, 8090],
                         noauth_local_webserver=False,
                         logging_level='ERROR')

        credentials = run_flow(flow, storage, args)
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
    # FIXME: does not work if the google api is not installed
    main(**kwargs)
