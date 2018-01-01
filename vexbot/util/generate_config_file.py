import os
import logging
import inspect
import configparser
import pkg_resources
from os import path

from vexbot.util.get_vexdir_filepath import get_config_dir


def _systemd_user_filepath() -> str:
    config = get_config_dir()
    config = path.join(config, 'systemd', 'user')
    os.makedirs(config, exist_ok=True)
    return path.join(config, 'vexbot.service')


def _get_vexbot_robot() -> str:
    for entry_point in pkg_resources.iter_entry_points('console_scripts'):
        if entry_point.name == 'vexbot_robot' and entry_point.dist.project_name == 'vexbot':
            # TODO: call the `require` function first and provide an installer
            # so that we can get the matching `Distribution` instance?
            return inspect.getsourcefile(entry_point.resolve())

    raise RuntimeError('Entry point for `vexbot_robot` not found! Are you '
                       'sure it\'s installed?')


def config(filepath=None, remove_config=False):
    if filepath is None:
        filepath = _systemd_user_filepath()
    if path.exists(filepath) and remove_config:
        os.unlink(filepath)
    elif path.exists(filepath) and not remove_config:
        logging.error(' Configuration filepath already exsists at: %s',
                      filepath)
        return

    parser = configparser.ConfigParser()
    parser['Unit'] = {'Description': 'Helper Bot'}
    parser['Service'] = {'Type': 'simple',
                         'ExecStart': _get_vexbot_robot(),
                         'StandardOutput': 'syslog',
                         'StandardError': 'syslog'}

    with open(filepath, 'w') as f:
        parser.write(f)

    print('Config file created at: {}'.format(filepath))


def main():
    remove_config = input('Remove config if present? Y/n: ')
    remove_config = remove_config.lower()
    if remove_config in ('y', 'yes', 'ye'):
        remove_config = True
    else:
        remove_config = False

    config(remove_config=remove_config)


if __name__ == '__main__':
    main()
