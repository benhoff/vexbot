import os
import sys
from subprocess import Popen
from vexbot.util import _get_config


# need a way to input the code |solved for shell input case|
# need to store code permenantly |need to metadata to this|
# need to load code, w/ metadata

## compile function allows us to compile 'single' and 'exec'

# Create error catching
# feeback loop
##  Need to implement pub-sub filtering |CHECK THE BOX|

# need to store the code in a file
# need to load the code somehow
# run the code

class CommandManager:
    # Think about passing in an adapter? And hooking up a command manager to
    # adapter
    def __init__(self, robot):
        self.r = robot
        self._commands = ['start', 'restart', 'kill', 'killall',
                          'list']

    def parse_commands(self, command):
        commands = command.split()
        command = commands.pop(0)
        if command == 'start':
            self.r.subprocess_manager.start(commands)
        elif command == 'restart':
            self.r.subprocess_manager.restart(commands)
        elif command == 'kill':
            self.r.subprocess_manager.kill(commands)
        elif command == 'killall':
            self.r.subprocess_manager.killall()
            sys.exit()
        elif command == 'list':
            lists = [x for x in self.r.subprocess_manager._subprocess.keys()]
            if lists:
                print(*lists)
                print('vexbot: ', end=None)
        elif command == 'commands':
            print(*self._commands)
            print('vexbot: ', end=None)
        elif command == 'restartbot':
            config = _get_config()
            settings_path = config.get('settings_path')
            directory = os.path.abspath(os.path.dirname(__file__))
            robot = os.path.join(directory, 'robot.py')
            args = (sys.executable,
                    '-c',
                    "import time\nimport sys\nfrom subprocess import Popen\ntime.sleep(1)\nPopen((sys.executable, '{}', '--settings_path', '{}'))".format(robot, settings_path))

            Popen(args)
            sys.exit()
