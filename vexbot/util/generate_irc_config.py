import logging
import inspect
import pkg_resources
import configparser
from os import path
import getpass

from vexbot.util.get_vexdir_filepath import get_config_dir


def _get_irc() -> str:
    for entry_point in pkg_resources.iter_entry_points('console_scripts'):
        if entry_point.name == 'vexbot_irc' and entry_point.dist.project_name == 'vexbot':
            # TODO: call the `require` function first and provide an installer
            # so that we can get the matching `Distribution` instance?
            return inspect.getsourcefile(entry_point.resolve())

    raise RuntimeError('Entry point for `vexbot_robot` not found! Are you '
                       'sure it\'s installed?')


def _irc_systemd_filepath(service_name: str=None) -> str:
    config = get_config_dir()
    config = path.join(config, 'systemd', 'user')
    os.makedirs(config, exist_ok=True)
    if service_name is None:
        service_name = 'irc'

    service_name = '{}.service'.format(service_name)
    return path.join(config, service_name)


def _generate_systemd_unit(filepath: str=None,
                           config_filepath: str=None,
                           service_name: str=None,
                           remove_config: bool=False):

    assert not filepath and service_name, 'Cannot pass in both a filepath name and a service'
    if filepath is None:
        filepath = _irc_systemd_filepath()
    if path.exists(filepath) and remove_config:
        os.unlink(filepath)
    elif path.exists(filepath) and not remove_config:
        logging.error(' Configuration filepath already exsists at: %s',
                      filepath)
        return

    binary = _get_irc()

    start = '{} {}'.format(binary, config_filepath)

    parser = configparser.ConfigParser()
    parser['Unit'] = {'Description': 'IRC adapter for vexbot'}
    parser['Service'] = {'Type': 'dbus',
                         'ExecStart': start,
                         'StandardOutput': 'syslog',
                         'StandardError': 'syslog'}

    with open(filepath, 'w') as f:
        parser.write(f)


def _generate_irc_config(service_name: str=None,
                         filepath: str=None,
                         remove_config: bool=False) -> str:

    nick = input('Desired nick [vexbot]: ')
    if not nick:
        nick = 'vexbot'
    password = getpass.getpass()
    confirm = getpass.getpass('Confirm Password: ')

    while not password == confirm:
        confirm = ''
        print('Passwords did not match!')
        password = getpass.getpass()
        confirm = getpass.getpass('Confirm Password: ')

    host = input('Host: ')
    port = input('Port [6667]: ')
    if not port:
        port = 6667
    else:
        port = int(port)
    autojoin_channels = input('Channels to autojoin [#python]: ')
    if not autojoin_channels:
        autojoin_channels = '#python'

    parser = configparser.ConfigParser()
    parser['bot'] = {'nick': nick,
                     'password': password,
                     'host': host,
                     'port': port,
                     includes: 'irc3.plugins.core irc3.plugins.autojoins',
                     cmd: '!',
                     service_name = service_name}

    with open(filepath, 'w') as f:
        parser.write(f)


def config(systemd_filepath: str=None,
           irc_config_filepath: str=None,
           service_name: str=None,
           remove_config: bool=False):

    fp = _generate_irc_config(irc_config_filepath, remove_config)
    _generate_systemd_unit(systemd_filepath, service_name, remove_config)


    print('Config file created at: {}'.format(filepath))


def main():
    # FIXME: two service files here...
    remove_config = input('Remove config if present? Y/n: ')
    remove_config = remove_config.lower()
    if remove_config in ('y', 'yes', 'ye'):
        remove_config = True
    else:
        remove_config = False

    service_name = input('Service name? [irc]')

    config(remove_config=remove_config)
