import sys
import logging

import pluginmanager

from vexmessage import decode_vex_message

from vexbot.messaging import Messaging
from vexbot.argenvconfig import ArgEnvConfig
from vexbot.command_managers import BotCommandManager
from vexbot.subprocess_manager import SubprocessManager


class RobotSettings:
    def __init__(self,
                 publish_address=None,
                 subscribe_address=None,
                 monitor_address=None):

        self.publish_address = publish_address
        self.subscribe_address = subscribe_address
        self.monitor_address = monitor_address

    @classmethod
    def create_from_configuration(cls, configuration):
        pass


class Robot:
    def __init__(self, settings: RobotSettings, bot_name="vex"):
        # get the settings path and then load the settings from file
        self.messaging = Messaging(settings)

        # create the plugin manager
        self.plugin_manager = pluginmanager.PluginInterface()
        # add the entry points of interest
        self.plugin_manager.add_entry_points(('vexbot.plugins',
                                              'vexbot.adapters'))

        # create the subprocess manager and add in the plugins
        self.subprocess_manager = SubprocessManager()
        _update_plugins(settings,
                        self.subprocess_manager,
                        self.plugin_manager)

        subprocesses_to_start = settings.get('startup_adapters', [])
        subprocesses_to_start.extend(settings.get('startup_plugins', []))
        self.subprocess_manager.start(subprocesses_to_start)

        self.name = bot_name
        self._logger = logging.getLogger(__name__)
        self.command_manager = BotCommandManager(robot=self)
        try:
            import setproctitle
            setproctitle.setproctitle(bot_name)
        except ImportError:
            pass

    def run(self):
        while True:
            frame = self.messaging.subscription_socket.recv_multipart()
            msg = None
            try:
                msg = decode_vex_message(frame)
            except Exception:
                pass
            if msg:
                # Right now this is hardcoded into being only
                # the shell adapter
                # change this to some kind of auth code
                if ((msg.source == 'shell' or
                     msg.source == 'command_line') and msg.type == 'CMD'):

                    self.command_manager.parse_commands(msg)



def _update_plugins(self,
                    settings,
                    subprocess_manager,
                    plugin_manager):

    """
    Helper process which loads the plugins from the entry points
    """
    collect_ep = plugin_manager.collect_entry_point_plugins
    plugins, plugin_names = collect_ep()
    plugins = [plugin.__file__ for plugin in plugins]
    for plugin, name in zip(plugins, plugin_names):
        subprocess_manager.register(name,
                                    sys.executable,
                                    {'filepath': plugin})

    for name in plugin_names:
        try:
            plugin_settings = settings[name]
        except KeyError:
            plugin_settings = {}

        subprocess_manager.update_settings(name, plugin_settings)


def _get_config():
    config = ArgEnvConfig()
    config.add_argument('--settings_path',
                        default=None,
                        action='store')

    config.add_argument('--subscribe_address',
                        default=None,
                        action='store')

    config.add_argument('--publish_address',
                        default=None,
                        action='store')

    config.add_argument('--monitor_address',
                        default=None,
                        action='store')

    return config

"""
settings_path = configuration.get('settings_path')
if settings_path:
    settings = configuration.load_settings(settings_path)
else:
    settings = {}
"""


if __name__ == '__main__':
    config = _get_config()
    sp = '--settings_path'
    if config.get(sp):
        config.update_settings(config.get(sp))

    robot_settings = RobotSettings.create_from_configuration(config)
    robot = Robot(robot_settings)
    robot.run()
