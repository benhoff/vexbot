import sys
import logging
import textwrap
import argparse

try:
    import setproctitle
except ImportError:
    pass

import pluginmanager

from vexmessage import decode_vex_message

from vexbot.messaging import Messaging
from vexbot.settings_manager import SettingsManager
from vexbot.command_managers import BotCommandManager
from vexbot.subprocess_manager import SubprocessManager


class Robot:
    def __init__(self, context='default'):
        name = __name__ if __name__ != '__main__' else 'vexbot.robot'
        self._logger = logging.getLogger(name)
        self.settings_manager = SettingsManager(context=context)
        robot_model = self.settings_manager.get_robot_model()
        if robot_model is None:
            s = textwrap.dedent('The context: `{}` was not found in settings. Be sure to '
                                'create this using `create_robot_settings` in the shell adapter, or another '
                                'fashion, and relaunch vexbot. Exiting robot now.'.format(context))

            self._logger.warn(textwrap.fill(s, initial_indent='', subsequent_indent='    '))
            sys.exit(1)

        self.messaging = Messaging(context,
                                   robot_model.zmq_publish_address,
                                   robot_model.zmq_subscription_addresses,
                                   robot_model.zmq_monitor_address,
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

        adapters = collect_ep(return_dict=True)
        self.settings_manager.update_modules(adapters.keys())
        for name, adapter in adapters.items():
            adapters[name] = value.__file__

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
        try:
            setproctitle.setproctitle(robot_model.name)
        except NameError: # this will happen if setproctitil is not installed
            pass

    def run(self):
        self.messaging.start()
        """
        # if not self.messaging.subscription_active():
        if True:
            logging.error('Subscription socket not set for context, check/set before running robot')
            return
        """
        while True and self.messaging.running():
            frame = self.messaging.subscription_socket.recv_multipart()
            msg = None
            try:
                msg = decode_vex_message(frame)
            except Exception:
                pass
            if msg and self.messaging.running():
                # Right now this is hardcoded into being only
                # the shell adapter
                # change this to some kind of auth code
                if ((msg.source == 'shell' or
                     msg.source == 'command_line') and msg.type == 'CMD'):

                    self.command_manager.parse_commands(msg)

        if not self.messaging.running():
            s = textwrap.fill('Could not bind the ports. Either another '
                              'instance of vexbot is running or another '
                              'program is bound to the address. Exiting this'
                              ' bot',
                              initial_indent='',
                              subsequent_indent='    ')

            self._logger.error(s)
            sys.exit()


def _get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('context', default='default', nargs='?')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = vars(_get_args())
    robot = Robot(*args.values())
    robot.run()
