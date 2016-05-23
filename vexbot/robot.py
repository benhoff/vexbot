import sys
import types
import logging
import pickle

import zmq
import zmq.devices
import pluginmanager

from vexbot.messaging import Messaging
from vexbot.argenvconfig import ArgEnvConfig
from vexbot.command_manager import CommandManager
from vexbot.subprocess_manager import SubprocessManager


class Robot:
    def __init__(self, configuration, bot_name="vex"):
        self.command_manager = CommandManager(robot=self)
        # get the settings path and then load the settings from file
        settings_path = configuration.get('settings_path')
        settings = configuration.load_settings(settings_path)
        self.messaging = Messaging(settings)

        # create the plugin manager
        self.plugin_manager = pluginmanager.PluginInterface()
        # add the entry points of interest
        self.plugin_manager.add_entry_points(('vexbot.plugins',
                                              'vexbot.adapters'))

        # create the subprocess manager and add in the plugins
        self.subprocess_manager = SubprocessManager()
        self._update_plugins(settings,
                             self.subprocess_manager,
                             self.plugin_manager)

        subprocesses_to_start = settings.get('startup_adapters', [])
        subprocesses_to_start.extend(settings.get('startup_plugins', []))
        self.subprocess_manager.start(subprocesses_to_start)

        self.name = bot_name
        self._logger = logging.getLogger(__name__)
        name = b'vexbot'

    def run(self):
        while True:
            frame = self.messaging._monitor_socket.recv()
            try:
                frame = pickle.loads(frame)
            except (pickle.UnpicklingError, EOFError):
                frame = None
            if frame:
                frame_len = len(frame)
                if frame[1] == 'CMD':
                    self.command_manager.parse_commands(frame[2])

    def _update_plugins(self,
                        settings,
                        subprocess_manager=None,
                        plugin_manager=None):
        """
        Helper process which loads the plugins from the entry points
        """
        if subprocess_manager is None:
            subprocess_manager = self.subprocess_manager
        if plugin_manager is None:
            plugin_manager = self.plugin_manager

        collect_ep = plugin_manager.collect_entry_point_plugins
        plugins, plugin_names = collect_ep()
        plugins = [plugin.__file__ for plugin in plugins]
        subprocess_manager.register(plugin_names, plugins)

        for name in plugin_names:
            try:
                plugin_settings = settings[name]
                values = []
                for k_v in plugin_settings.items():
                    values.extend(k_v)
            except KeyError:
                values = []
            self.subprocess_manager.update(name, setting=values)


def _get_config():
    config = ArgEnvConfig()
    config.add_argument('--settings_path',
                        default='settings.yml',
                        action='store')

    return config


if __name__ == '__main__':
    config = _get_config()
    robot = Robot(config)
    robot.run()
