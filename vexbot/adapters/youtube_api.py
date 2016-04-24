import sys
import argparse
from time import sleep
from chatimusmaximus.util import youtube_authentication
from chatimusmaximus.communication_protocols.communication_messaging import ZmqMessaging # flake8: noqa


def main(client_secret_filepath, socket_address):
    messaging = ZmqMessaging('youtube', socket_address)
    scope = ['https://www.googleapis.com/auth/youtube',
             'https://www.googleapis.com/auth/youtube.force-ssl',
             'https://www.googleapis.com/auth/youtube.readonly']

    youtube_api = youtube_authentication(client_secret_filepath, scope)
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


if __name__ == '__main__':
    kwargs = _get_kwargs()
    # OAuth2 lib has some argparse functionality that conflicts with ours
    # delete ours for ease of programming
    for _ in range(4):
        del sys.argv[1]
    main(**kwargs)
