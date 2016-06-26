import os
import sys
import string
from subprocess import Popen
from vexbot.commands.start_vexbot import _get_config


# need a way to input the code |solved for shell input case|
# need to store code permenantly |need to metadata to this|
# need to load code, w/ metadata

# compile function allows us to compile 'single' and 'exec'

# Create error catching
# feeback loop
#  Need to implement pub-sub filtering |CHECK THE BOX|

# need to store the code in a file
# need to load the code somehow
# run the code

INDENTCHARS = string.ascii_letters + string.digits + '_'

class CommandManager:
    def __init__(self, robot):
        self.r = robot
        self._command_list = ['start', 'restart', 'kill', 'killall',
                              'list', 'alive']

        self._commands = {}
        self.indentchars = INDENTCHARS
        self._commands['start'] = robot.subprocess_manager.start
        self._commands['restart'] = robot.subprocess_manager.restart
        self._commands['kill'] = robot.subprocess_manager.kill

    def parse_commands(self, msg):
        command = msg.contents[0].strip()
        if not command:
            return
        i, n = 0, len(command)
        while i < n and command[i] in self.indentchars: i = i + 1
        command, arg = command[:i], command[i:].strip()
        commands = arg.split()

        callback = self._commands.get(command, None)
        if callback:
            callback(commands)
            return

        if command == 'killall':
            self.r.subprocess_manager.killall()
            sys.exit()
        elif command == 'help':
            self.r.messaging.send_response(*self._commands,
                                           target=msg.source,
                                           original=command)

        elif command == 'list':
            lists = [x for
                     x in
                     self.r.subprocess_manager.registered_subprocesses()]

            if lists:
                self.r.messaging.send_response(*lists,
                                               target=msg.source,
                                               original=command)

        elif command == 'commands':
            self.r.messaging.send_response(*self._commands,
                                           target=msg.source,
                                           original=command)

        elif command == 'alive':
            values = list(self.r.subprocess_manager.registered_subprocesses())
            if values:
                try:
                    values.remove(msg.source)
                except ValueError:
                    pass
                for v in values:
                    self.r.messaging.send_command('alive', target=v)
        elif command == 'record':
            self.r.messaging.send_command(('record',))
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
