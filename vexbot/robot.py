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


class Robot:
    def __init__(self, profile='default'):
        name = __name__ if __name__ != '__main__' else 'vexbot.robot'
        self._logger = logging.getLogger(name)
        self.settings_manager = SettingsManager(profile=profile)
        robot_model = self.settings_manager.get_robot_model()
        if robot_model is None:
            s = textwrap.dedent('The profile: `{}` was not found in settings. Be sure to '
                                'create this using `create_robot_settings` in the shell adapter, or another '
                                'fashion, and relaunch vexbot. Exiting robot now.'.format(profile))

            self._logger.warn(textwrap.fill(s, initial_indent='', subsequent_indent='    '))
            sys.exit(1)

        self.messaging = Messaging(profile,
                                   robot_model.zmq_publish_address,
                                   robot_model.zmq_subscription_addresses,
                                   robot_model.zmq_heartbeat_address)

        # create the plugin manager
        self.plugin_manager = pluginmanager.PluginInterface()

        # create the subprocess manager and add in the plugins
        self.subprocess_manager = SubprocessManager(self.settings_manager)

        # Note: pluginmanager should probably return a `dict` instead of
        # two lists. Should probably fix
        collect_ep = self.plugin_manager.collect_entry_point_plugins
        plugin_settings = collect_ep('vexbot.adapter_settings',
                                     return_dict=True)

        # self.plugin_manager.add_entry_points(('vexbot.plugins',))

        adapters = collect_ep(('vexbot.adapters',), return_dict=True)
        self.settings_manager.update_modules(adapters.keys())
        for name, adapter in adapters.items():
            adapters[name] = adapter.__file__

            self.subprocess_manager.register(name,
                                             sys.executable,
                                             {'filepath': adapter.__file__})

            try:
                # using convention to snag plugin settings.
                # expect that settings will be in the form of
                # `adapter_name` + `_settings`
                # I.E. `irc_settings` for adapter `irc`
                setting_name = name + '_settings'
                setting_class = plugin_settings[setting_name]
            except KeyError:
                setting_class = None

            self.subprocess_manager.set_settings_class(name, setting_class)

        startup_adapters = self.settings_manager.get_startup_adapters()
        self.subprocess_manager.start(startup_adapters)

        self.name = robot_model.name
        self.command_manager = BotCommandManager(robot=self)
        if setproctitle:
            setproctitle.setproctitle(robot_model.name)

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
    parser.add_argument('profile', default='default', nargs='?')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = vars(_get_args())
    robot = Robot(*args.values())
    robot.run()
