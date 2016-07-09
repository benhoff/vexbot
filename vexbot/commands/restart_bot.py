import os
import sys

from subprocess import Popen
from vexbot.commands.start_vexbot import _get_config


def restart_bot():
    """
    restarts vexbot
    """
    config = _get_config()
    settings_path = config.get('settings_path')
    directory = os.path.abspath(os.path.dirname(__file__))
    robot = os.path.abspath(os.path.join(directory, '..', 'robot.py'))
    s = "import time\nimport sys\nfrom subprocess import Popen\ntime.sleep(1" \
        ")\nPopen((sys.executable, '{}', '--settings_path', '{}'))"

    s = s.format(robot, settings_path)
    args = (sys.executable,
            '-c',
            s)

    Popen(args)
    sys.exit()
