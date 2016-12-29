import sys
import logging
import textwrap
import argparse

try:
    import setproctitle
except ImportError:
    setproctitle = False

import pluginmanager

from vexmessage import decode_vex_message

from vexbot.messaging import Messaging
from vexbot.settings_manager import SettingsManager
from vexbot.command_managers import BotCommandManager
from vexbot.subprocess_manager import SubprocessManager
from vexbot.util.get_config import get_config


class Robot:
    def __init__(self,
                 subprocess_manager=None,
                 messaging=None):

        log_name = __name__ if __name__ != '__main__' else 'vexbot.robot'
        self._logger = logging.getLogger(log_name)

        self.subprocess_manager = subprocess_manager
        self.messaging = messaging

        self.command_manager = BotCommandManager(robot=self)
        if setproctitle:
            setproctitle.setproctitle(name)

    def run(self):
        self.messaging.start()
        for msg in self.messaging.run():
            # Right now this is hardcoded into being only
            # the shell adapter
            # change this to some kind of auth code
            if ((msg.source == 'shell' or
                 msg.source == 'command_line') and msg.type == 'CMD'):

                self.command_manager.parse_commands(msg)


def _get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('name', default='vexbot', nargs='?')
    parser.add_argument('profile', default='default', nargs='?')
    args = parser.parse_args()
    return args


def setup_robot():
    settings = get_config()
    vexbot_settings = settings.get('vexbot', {'profile': 'default'})
    profile = vexbot_settings.get('profile', 'default')

    # setting the profile interfaces with the database
    settings_manager = SettingsManager(profile=profile,
                                       config_settings=settings)

    robot_model = settings_manager.get_robot_model()

    if robot_model is None:
        # FIXME: fix the instructions
        s = textwrap.dedent('The profile: `{}` was not found in the settings database'
                            'Be sure to create this using `create_robot_se'
                            'ttings` in the shell adapter, or running `$ vexbot_quickstart` from the terminal.'
                            'Exiting robot now.'.format(profile))

        logging.warn(textwrap.fill(s,
                     initial_indent='',
                     subsequent_indent='    '))

        sys.exit(1)

    messaging = Messaging(profile,
                          robot_model.zmq_publish_address,
                          robot_model.zmq_subscription_addresses,
                          robot_model.zmq_heartbeat_address)

    subprocess_manager = SubprocessManager(settings_manager)

    # Note: pluginmanager should probably return a `dict` instead of
    # two lists. Should probably fix

    startup_adapters = settings_manager.get_startup_adapters()
    subprocess_manager.start(startup_adapters)

    robot = Robot(subprocess_manager=subprocess_manager,
                  messaging=messaging)

    return robot


if __name__ == '__main__':
    args = vars(_get_args())
    robot = setup_robot()
    robot.run()
