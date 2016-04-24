#!/usr/bin/env python3
import sys
import atexit
from os import path
from subprocess import Popen
from vexbot.adapters.shell import main as shell_main


"""
def _get_kargs():
    parser = argparse.ArgumentParser(description='Vex, personal assistant')
    parser.add_argument('--debug',
                        action='store_true',
                        help='Show debug messages')

    args = parser.parse_args()
    return vars(args)
"""
def _kill_subprocess(process):
    process.terminate()


if __name__ == "__main__":
    # Need to start the robot program as a subprocess
    # Grab the filepath
    root_directory = path.abspath(path.dirname(__file__))
    robot_filepath = path.join(root_directory, 'robot.py')

    # Start the subprocess
    main_robot_args = (sys.executable, robot_filepath)
    main_subprocess = Popen(main_robot_args)

    # make sure to kill the subprocess when the main is killed?
    atexit.register(_kill_subprocess, main_subprocess)

    # Launch the shell interface
    shell_main()
