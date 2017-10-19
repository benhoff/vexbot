import argparse
import configparser

from vexbot.adapters.socket_io import WebSocket


def _get_args():
    # FIXME: need to ensure that these values are passed in
    parser = argparse.ArgumentParser()
    parser.add_argument('configuration_file')
    return parser.parse_args()


def main():
    args = _get_args()
    config = configparser.ConfigParser() 
    config.read(args.configuration_file)
    kwargs = config['socket_io']
    client = WebSocket(**kwargs)
    client.run_forever()


if __name__ == '__main__':
    main()
