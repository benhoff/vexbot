import sys
from os import path
from subprocess import Popen
from zmq import ZMQError
from vexbot.argenvconfig import ArgEnvConfig
from vexbot.messaging import Messaging


def _get_config():
    config_manager = ArgEnvConfig()
    config_manager.add_argument('--settings_path',
                                default='settings.yml',
                                action='store')

    return config_manager


def start_vexbot():
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

        Popen(main_robot_args)

    return settings
