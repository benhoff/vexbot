import sys
import logging
import textwrap
import argparse

import zmq
import pluginmanager

from vexmessage import decode_vex_message

from vexbot.messaging import Messaging
from vexbot.settings_manager import SettingsManager
from vexbot.command_managers import BotCommandManager
from vexbot.subprocess_manager import SubprocessManager


class Robot:
    def __init__(self, context='default'):
        self.settings_manager = SettingsManager(context=context)
        # Handle None case
        robot_settings = self.settings_manager.get_robot_settings()
        if robot_settings is None:
            s = textwrap.fill('Context: `{}` not found in settings, be sure to '
                              'create this using shell adapter, or another '
                              'fashion'.format(context))

            logging.error(s)
            sys.exit(1)

        self.messaging = Messaging(context,
                                   robot_settings.publish_address,
                                   robot_settings.subscribe_address,
                                   robot_settings.monitor_address)

        # create the plugin manager
        self.plugin_manager = pluginmanager.PluginInterface()
        # add the entry points of interest

        # create the subprocess manager and add in the plugins
        self.subprocess_manager = SubprocessManager(self.settings_manager)

        # Note: pluginmanager should probably return a `dict` instead of
        # two lists. Should probably fix
        collect_ep = self.plugin_manager.collect_entry_point_plugins
        plugin_settings, ps_names = collect_ep('vexbot.adapter_settings')
        name_setting = zip(ps_names, plugin_settings)
        plugin_settings = {name: setting for name, setting in name_setting}

        self.plugin_manager.add_entry_points('vexbot.adapters')

        adapters, names = collect_ep()
        adapters = {name: p.__file__ for p, name in zip(adapters, names)}
        print(adapters)

        for name, adapter in adapters.items():
            self.subprocess_manager.register(name,
                                             sys.executable,
                                             {'filepath': adapter})

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

        self.name = robot_settings.name
        self._logger = logging.getLogger(__name__)
        self.command_manager = BotCommandManager(robot=self)
        try:
            import setproctitle
            setproctitle.setproctitle(robot_settings.name)
        except ImportError:
            pass

    def run(self):
        self.messaging.start()
        """
        # if not self.messaging.subscription_active():
        if True:
            logging.error('Subscription socket not set for context, check/set before running robot')
            return
        """

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

def _get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('context', default='default', nargs='?')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = vars(_get_args())
    robot = Robot(*args.values())
    robot.run()
