import os
import sys

from subprocess import Popen


def restart_bot():
    """
    restarts vexbot
    """
    directory = os.path.abspath(os.path.dirname(__file__))
    robot = os.path.abspath(os.path.join(directory, '..', 'robot.py'))
    s = "import time\nimport sys\nfrom subprocess import Popen\ntime.sleep(1" \
        ")\nPopen((sys.executable, '{}'))"

    s = s.format(robot)
    args = (sys.executable,
            '-c',
            s)

    Popen(args)
    sys.exit()
