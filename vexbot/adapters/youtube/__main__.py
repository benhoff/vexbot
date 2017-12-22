import argparse
from configparser import ConfigParser

from vexbot.adapters.youtube import Youtube


def _get_kwargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('client_secret_filepath')
    args = parser.parse_args()
    kwargs = vars(args)

    return kwargs

def main(client_secret_filepath: str):
    config_parser = ConfigParser.read(client_secret_filepath)
    youtube = Youtube()
    youtube.run()


if __name__ == '__main__':
    kwargs = _get_kwargs()
    main(**kwargs)
