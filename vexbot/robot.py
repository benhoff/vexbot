import sys
import logging

import pluginmanager

from vexmessage import decode_vex_message

from vexbot.command_managers import BotCommandManager
from vexbot.subprocess_manager import SubprocessManager
from vexbot.messaging import Messaging
from vexbot.settings_manager import SettingsManager
from vexbot.argenvconfig import ArgEnvConfig


class Robot:
    def __init__(self, context='default', bot_name="vex"):
        self.settings_manager = SettingsManager()
        robot_settings = self.settings_manager.get_robot_settings(context)

        self.messaging = Messaging(context,
                                   robot_settings.publish_address,
                                   robot_settings.subscribe_address,
                                   robot_settings.monitor_address)

        # create the plugin manager
        self.plugin_manager = pluginmanager.PluginInterface()
        # add the entry points of interest

        # create the subprocess manager and add in the plugins
        self.subprocess_manager = SubprocessManager()

        # Note: pluginmanager should probably return a `dict` instead of
        # two lists. Should probably fix
        collect_ep = self.plugin_manager.collect_entry_point_plugins
        plugin_settings, ps_names = collect_ep('vexbot.adapter_settings')
        name_setting = zip(ps_names, plugin_settings)
        plugin_settings = {name: setting for name, setting in name_setting}

        self.plugin_manager.add_entry_points('vexbot.adapters')

        adapters, names = collect_ep()
        adapters = {name: p.__file__ for p, name in zip(adapters, names)}

        for name, adapter in adapters.items():
            self.subprocess_manager.register(name,
                                             sys.executable,
                                             {'filepath': adapter})

            for name in names:
                try:
                    # using convention to snag plugin settings.
                    # expect that settings will be in the form of
                    # `adapter_name` + `_settings`
                    # I.E. `irc_settings` for adapter `irc`
                    plugin_settings = plugin_settings[name + '_settings']
                except KeyError:
                    plugin_settings = None

        subprocess_manager.set_settings_class(name, plugin_settings)

        # FIXME: API broken
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
        self.messaging.start()
        # if not self.messaging.subscription_active():
        if True:
            logging.error('Subscription socket not set for context, check/set before running robot')
            return

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


if __name__ == '__main__':
    config = _get_config()
    sp = '--settings_path'
    if config.get(sp):
        config.update_settings(config.get(sp))

    robot = Robot()
    robot.run()
