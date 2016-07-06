import sys
import os
from os import path
from subprocess import Popen
import zmq
from vexbot.argenvconfig import ArgEnvConfig


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

    if not already_running:
        socket.disconnect(address_to_check)

    return already_running


def start_vexbot():
    """
    starts up an instance of vexbot if one isn't running currently
    """
    config = _get_config()
    settings_path = config.get('settings_path')
    settings = config.load_settings(settings_path)
    process = None

    if not _running(settings.get('monitor_address')):
        root_directory = path.abspath(path.join(path.dirname(__file__), '..'))
        robot_filepath = path.join(root_directory, 'robot.py')

        # Start the subprocess
        main_robot_args = (sys.executable,
                           robot_filepath,
                           '--settings_path',
                           settings_path)

        process = Popen(main_robot_args)

    return settings, process
