#!/usr/bin/env python3
import sys
from os import path
from subprocess import Popen
from zmq import ZMQError
from vexbot.argenvconfig import ArgEnvConfig
from vexbot.adapters.shell import main as shell_main
from vexbot.messaging import Messaging


def _get_config():
    config_manager = ArgEnvConfig()
    config_manager.add_argument('--settings_path',
                                default='settings.yml',
                                action='store')

    return config_manager


if __name__ == "__main__":
    config = _get_config()
    settings_path = config.get('settings_path')
    settings = config.load_settings(settings_path)

    messaging = Messaging()

    already_running = False
    pub_address = settings.get('publish_address',
                               'tcp://127.0.0.1:4001')

    try:
        messaging.pub_socket.bind(pub_address)
    except ZMQError:
        already_running = True

    if not already_running:
        messaging.pub_socket.disconnect(pub_address)
        root_directory = path.abspath(path.dirname(__file__))
        robot_filepath = path.join(root_directory, 'robot.py')

        # Start the subprocess
        main_robot_args = (sys.executable,
                           robot_filepath,
                           '--settings_path',
                           settings_path)

        main_subprocess = Popen(main_robot_args)

    shell_settings = settings['shell']
    for key in set(shell_settings.keys()):
        value = shell_settings.pop(key)
        shell_settings[key[2:]] = value

    # Launch the shell interface
    shell_main(**shell_settings)
