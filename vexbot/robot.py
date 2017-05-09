import sys
import logging
import textwrap

try:
    import setproctitle
except ImportError:
    setproctitle = False

import vexbot.util as util

from vexbot.messaging import Messaging
from vexbot.settings_manager import SettingsManager
from vexbot.command_managers import BotCommandManager
from vexbot.adapter_interface import AdapterInterface
from vexbot.subprocess_manager import SubprocessManager


class Robot:
    def __init__(self,
                 messaging: Messaging=None,
                 adapter_interface: AdapterInterface=None,
                 command_manager: BotCommandManager=None):

        # Messaging is too complex to setup as default
        self.messaging = messaging
        if adapter_interface is None:
            adapter_interface = AdapterInterface(SettingsManager(),
                                                 SubprocessManager())

        if command_manager is None:
            command_manager = BotCommandManager(robot=self)

        self.adapter_interface = adapter_interface
        self.command_manager = command_manager

        log_name = self._get_log_name()
        self._logger = logging.getLogger(log_name)

    def run(self):
        self.messaging.start()
        for msg in self.messaging.run():
            # TODO: add in authentication
            if msg.type == 'CMD':
                self.command_manager.parse_commands(msg)

    def _get_log_name(self):
        return __name__ if __name__ != '__main__' else 'vexbot.robot'


def main(**kwargs):
    """
    `configuration_filepath`
    """
    # Get the command line arguments
    args = vars(util.get_args.get_args())

    # Get the configuration filepath
    config_filepath = args.get('configuration_filepath')
    # Get the configuration (possibly the default configuration)
    configuration = util.get_config.get_config(filepath=config_filepath)

    vexbot_settings = configuration.get('vexbot', {'robot_name': 'Vexbot'})
    robot_name = vexbot_settings.get('robot_name', 'Vexbot')

    port_config = configuration.get('vexbot_ports', {})
    messaging = Messaging(robot_name, kwargs=port_config)

    settings_manager = SettingsManager(port_configuration)

    adapter_interface = AdapterInterface(settings_manager,
                                         SubprocessManager())

    if setproctitle:
        setproctitle.setproctitle('vexbot')

    robot = Robot(messaging, adapter_interface)
    robot.run()


if __name__ == '__main__':
    main()
