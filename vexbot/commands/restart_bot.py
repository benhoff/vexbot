from subprocess import Popen
from vexbot.commands.start_vexbot import _get_config


def restart_bot():
    """
    restarts vexbot
    """
    config = _get_config()
    settings_path = config.get('settings_path')
    directory = os.path.abspath(os.path.dirname(__file__))
    robot = os.path.join(directory, 'robot.py')
    args = (sys.executable,
            '-c',
            "import time\nimport sys\nfrom subprocess import Popen\ntime.sleep(1)\nPopen((sys.executable, '{}', '--settings_path', '{}'))".format(robot, settings_path))

    Popen(args)
    sys.exit()
