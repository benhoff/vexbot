import sys
import atexit
import signal

try:
    pkg_resources.get_distribution('irc3')
except pkg_resources.DistributionNotFound:
    _IRC3_INSTALLED = False


if _IRC3_INSTALLED:
    import irc3

else:
    pass

def _get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--nick')
    parser.add_argument('--password')
    parser.add_argument('--host')
    parser.add_argument('--channel')
    parser.add_argument('--publish_address')
    parser.add_argument('--subscribe_address')
    parser.add_argument('--service_name')

    return parser.parse_args()


def main(**kwargs):
    """
    kwargs: 
        nick,
        password,
        host,
        channel,
        publish_address,
        subscribe_address,
        service_name
    """

    if not _IRC3_INSTALLED:
        logging.error('vexbot_irc requires `irc3` to be installed. Please install '
                      'using `pip install irc3`')

        sys.exit(1)

    command_line_kwargs = vars(_get_args())
    command_line_kwargs.update(kwargs)
    kwargs = command_line_kwargs
    if kwargs['nick'] is None or kwargs['host'] is None:
        logging.error('must supply a nick and a host!')
        sys.exit(1)

    irc_client = create_irc_bot(**kwargs)

    messaging = ZmqMessaging(kwargs['service_name'])
    messaging.start_messaging()

    # Duck type messaging onto irc_client, FTW
    irc_client.messaging = messaging

    # FIXME: don't use the bot command manager?
    # TODO: create an adapter specific one
    command_parser = BotCommands(messaging, SubprocessManager())
    irc_client.command_parser = command_parser

    irc_client.create_connection()
    irc_client.add_signal_handlers()
    event_loop = asyncio.get_event_loop()
    event_loop.set_debug(True)
    # asyncio.ensure_future(_check_subscription(irc_client))

    handle_close = _handle_close(messaging, event_loop)
    signal.signal(signal.SIGINT, handle_close)
    signal.signal(signal.SIGTERM, handle_close)
    event_loop.run_forever()
    event_loop.close()
    sys.exit()




if __name__ == '__main__':
    main()
