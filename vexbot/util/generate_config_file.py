from os import path
import inspect
import configparser
import pkg_resources


def _systemd_user_filepath() -> str:
    pass

def _get_vexbot_robot():
    for entry_point in pkg_resources.iter_entry_points('console_scripts'):
        if entry_point.name == 'vexbot_robot':
            # TODO: call the `require` function first and provide an installer
            # so that we can get the matching `Distribution` instance?
            return insepct.getsourcefile(entry_point.resolve())


def config(filepath=None):
    if filepath is None:
        filepath = _systemd_user_filepath()
    # FIXME: Handle
    if path.exists(filepath):
        pass

    parser = configparser.ConfigParser()
    parser['Unit'] = {'Description': 'Helper Bot'}
    parser['Service'] = {'Type': 'simple',
                         'ExecStart': _get_vexbot_robot(),
                         'StandardOutput': 'syslog',
                         'StandardError': 'syslog'}

    with open(filepath, 'w') as f:
        parser.write(f)
