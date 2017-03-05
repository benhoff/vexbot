import sys
from os import path
from subprocess import Popen


def start_vexbot(profile: str='default'):
    """
    starts up an instance of vexbot
    Returns: an instance of Popen
    """
    process = None

    root_directory = path.abspath(path.join(path.dirname(__file__), '..'))
    robot_filepath = path.join(root_directory, 'robot.py')

    # Start the subprocess
    main_robot_args = [sys.executable,
                       robot_filepath,
                       profile]

    process = Popen(main_robot_args)

    return process
