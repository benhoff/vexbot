import os
import logging
import inspect
import argparse
import configparser
import pkg_resources
from os import path

from vexbot.util.get_vexdir_filepath import get_config_dir


def _systemd_user_filepath() -> str:
    config = get_config_dir()
    config = path.join(config, 'systemd', 'user')
    os.makedirs(config, exist_ok=True)
    return path.join(config, 'youtube.service')


def _get_youtube_script_filepath() -> str:
    for entry_point in pkg_resources.iter_entry_points('console_scripts'):
        if entry_point.name == 'vexbot_youtube' and entry_point.dist.project_name == 'vexbot':
            # NOTE: we could call the `require` function first and provide an installer
            # so that we can get the matching `Distribution` instance?
            return inspect.getsourcefile(entry_point.resolve())

    raise RuntimeError('Entry point for `vexbot_robot` not found! Are you '
                       'sure it\'s installed?')


def _get_config_filepath() -> str:
    pass


def generate_config_file(filepath: str, client_secret_filepath: str):
    parser = configparser.ConfigParser()
    parser['youtube'] = {'client_secret_filepath': client_secret_filepath,
                         'service_name': 'youtube'}

    with open(filepath, 'w') as f:
        parser.write(f)

    print('Config file created at: {}'.format(filepath))


def config(client_secret_filepath: str, config_filepath: str=None, systemd_filepath: str=None):
    if config_filepath is None:
        config_filepath = _get_config_filepath()
    yt_filepath = _get_youtube_script_filepath()
    start = '{} {}'.format(yt_filepath, config)

    parser = configparser.ConfigParser()
    parser['Unit'] = {'Description': 'Helper Bot'}
    parser['Service'] = {'Type': 'dbus',
                         'ExecStart': start,
                         'StandardOutput': 'syslog',
                         'StandardError': 'syslog'}

    with open(systemd_filepath, 'w') as f:
        parser.write(f)

    print('Config file created at: {}'.format(filepath))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('client_secret_filepath')
    args = parser.parse_args()
    client_secret = args.client_secret_filepath

    remove_config = input('Remove config if present? Y/n: ')
    remove_config = remove_config.lower()
    if remove_config in ('y', 'yes', 'ye'):
        remove_config = True
    else:
        remove_config = False

    config(remove_config=remove_config, client_secret)


if __name__ == '__main__':
    main()
