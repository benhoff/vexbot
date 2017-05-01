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
from vexbot.util.get_config import get_config


class Robot:
    def __init__(self, settings_manager=None, messaging=None):
        log_name = __name__ if __name__ != '__main__' else 'vexbot.robot'
        self._logger = logging.getLogger(log_name)

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
    parser.add_argument('name', default='vexbot', nargs='?')
    args = parser.parse_args()
    return args


def setup_robot(configuration):
    vexbot_settings = configuration.get('vexbot', {})

    # setting the interfaces with the database
    settings_manager = SettingsManager(config_settings=configuration)
    robot_model = settings_manager.get_robot_model()

    # FIXME: fix the instructions
    if robot_model is None:
        s = textwrap.dedent('The profile: `{}` was not found in the settings database'
                            'Be sure to create this using `create_robot_se'
                            'ttings` in the shell adapter, or running `$ vexbot_quickstart` from the terminal.'
                            'Exiting robot now.'.format(profile))

        logging.warn(textwrap.fill(s,
                     initial_indent='',
                     subsequent_indent='    '))

        sys.exit(1)

    messaging = Messaging('vexbot',
                          robot_model.zmq_publish_address,
                          robot_model.zmq_subscription_addresses,
                          robot_model.zmq_heartbeat_address)

    settings_manager.start_startup_adapters()

    if setproctitle:
        setproctitle.setproctitle(name)

    robot = Robot(subprocess_manager=subprocess_manager,
                  messaging=messaging)

    return robot


if __name__ == '__main__':
    args = vars(_get_args())
    configuration = get_config()
    vexbot_settings = configuration.get('vexbot', {'name': 'vexbot'})
    name = vexbot_settings.get('name', 'vexbot')
    if setproctitle:
        setproctitle.setproctitle(name)
    robot = setup_robot(configuration)
    robot.run()
