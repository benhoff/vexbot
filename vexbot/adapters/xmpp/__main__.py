import argparse
import configparser
from vexbot.adapters.xmpp import XMPPBot
import logging


def _get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('configuration_file')
    return parser.parse_args()


def main():
    args = _get_args()
    config = configparser.ConfigParser() 
    config.read(args.configuration_file)
    kwargs = config['xmpp']

    jid = '{}@{}/{}'.format(kwargs['local'], kwargs['domain'], kwargs['resource'])
    xmpp_bot = XMPPBot(jid, **kwargs)
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)-8s %(message)s')
    xmpp_bot.connect()
    try:
        xmpp_bot.process(block=True)
    finally:
        xmpp_bot.disconnect()


if __name__ == '__main__':
    main()
