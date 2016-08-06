import sys
from os import path
from subprocess import Popen

from sqlalchemy import create_engine as _create_engine
from sqlalchemy.ext.declarative import declarative_base as _declarative_base

import zmq

from vexbot.argenvconfig import ArgEnvConfig
from vexbot.commands.create_vexdir import create_vexdir as _create_vexdir
from vexbot.util.get_settings_database_filepath import get_settings_database_filepath

_Base = _declarative_base()


def _create_database():
    _create_vexdir()
    database_filepath = get_settings_database_filepath()

    if not path.isfile(database_filepath):
        engine = _create_engine('sqlite:///{}'.format(database_filepath))
        _Base.metadata.create_all(engine)


def _get_config():
    config_manager = ArgEnvConfig()
    config_manager.add_argument('--settings_path',
                                environ='VEXBOT_SETTINGS',
                                action='store')

    return config_manager


def _running(address_to_check):
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    already_running = False
    try:
        socket.bind(address_to_check)
    except zmq.ZMQError:
        already_running = True

    """
    if not already_running:
        socket.disconnect(address_to_check)
    """

    return already_running


def start_vexbot(settings=None):
    """
    starts up an instance of vexbot if one isn't running currently
    """
    settings_path = None

    if settings is None:
        config = _get_config()
        settings_path = config.get('settings_path')
        # TODO: add in some handeling if no settings found
        settings = config.load_settings(settings_path)

    process = None

    if not _running(settings.get('monitor_address')):
        root_directory = path.abspath(path.join(path.dirname(__file__), '..'))
        robot_filepath = path.join(root_directory, 'robot.py')

        # Start the subprocess
        main_robot_args = [sys.executable,
                           robot_filepath]

        if settings_path:
            main_robot_args.extend(('--settings_path',
                                    settings_path))

        double_dash_settings = {}

        def double_dash(names, old_settings, new_settings):
            for name in names:
                if old_settings.get(name):
                    new_settings['--' + name] = old_settings.get(name)

        double_dash(('monitor_address',
                     'publish_address',
                     'subscribe_address'),
                    settings,
                    double_dash_settings)

        if double_dash_settings:
            [main_robot_args.extend(item) for item in double_dash_settings.items()]

        process = Popen(main_robot_args)

    return settings, process
