import sys
import logging
import textwrap
import argparse

try:
    import setproctitle
except ImportError:
    setproctitle = False

from vexbot.messaging import Messaging
from vexbot.settings_manager import SettingsManager
from vexbot.command_managers import BotCommandManager
import vexbot.util as util
from vexbot.util.get_config import get_config as _get_config


class Robot:
    def __init__(self, settings_manager=None, messaging=None):
        log_name = __name__ if __name__ != '__main__' else 'vexbot.robot'
        self._logger = logging.getLogger(log_name)
        if settings_manager is None:
            settings_manager = SettingsManager()

        self.settings_manager = settings_manager 
        self.messaging = messaging

        self.command_manager = BotCommandManager(robot=self)

    def run(self):
        self.messaging.start()
        for msg in self.messaging.run():
            # TODO: add in authentication
            if msg.type == 'CMD':
                self.command_manager.parse_commands(msg)


def _get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('robot_name', default='vexbot', nargs='?')
    parser.add_argument('configuration_filepath', nargs='?')
    args = parser.parse_args()
    return args


def _setup_messaging(botname, configuration):
    messaging = Messaging(botname,
                          protocol,
                          ip_address,
                          command_publish_port,
                          command_subscribe_port,
                          heartbeat_port,
                          control_port)

    return messaging


def main(**kwargs):
    """
    `configuration_filepath`
    """
    args = vars(_get_args())
    config_filepath = args.get('configuration_filepath')
    configuration = util.get_config.get_config(filepath=config_filepath)

    vexbot_settings = configuration.get('vexbot', {'robot_name': 'Vexbot'})
    robot_name = vexbot_settings.get('robot_name', 'Vexbot')
    if setproctitle:
        setproctitle.setproctitle('vexbot')

    port_config = configuration.get('vexbot_ports', {})
    messaging = Messaging(robot_name, kwargs=port_config)
    robot = Robot(messaging=messaging)
    robot.run()


if __name__ == '__main__':
    main()
