import logging as _logging

try:
    import setproctitle as _setproctitle
except ImportError:
    _setproctitle = False

import vexbot.util as _util

from vexbot.messaging import Messaging as _Messaging
from vexbot.settings_manager import SettingsManager as _SettingsManager
from vexbot.command_managers import BotCommandManager as _BotCommandManager
from vexbot.adapter_interface import AdapterInterface as _AdapterInterface
from vexbot.subprocess_manager import SubprocessManager as _SubprocessManager


class Robot:
    def __init__(self,
                 messaging: Messaging=None,
                 adapter_interface: AdapterInterface=None,
                 command_manager: BotCommandManager=None):

        # Messaging and adapter_interface are too complex to setup defaults
        self.messaging = messaging
        self.adapter_interface = adapter_interface

        if command_manager is None:
            command_manager = BotCommandManager(robot=self)

        self.command_manager = command_manager

        log_name = self._get_log_name()
        self._logger = _logging.getLogger(log_name)

    def run(self):
        self.messaging.start()
        for msg in self.messaging.run():
            # TODO: add in authentication
            if msg.type == 'CMD':
                self.command_manager.parse_commands(msg)

    def _get_log_name(self):
        return __name__ if __name__ != '__main__' else 'vexbot.robot'


def _port_configuration_helper(configuration: dict) -> dict:
    # Setup some default port configurations
    default_port_config = {'protocol': 'tcp',
                           'ip_address': '127.0.0.1',
                           'command_publish_port': 4000,
                           'command_subscribe_port': [4001,],
                           'heartbeat_port': 4002,
                           'control_port': 4003}

    # get the port settings out of the configuration, falling back on defaults
    port_config = configuration.get('ports', default_port_config)

    # update the defaults with the retrived port configs
    default_port_config.update(port_config)
    # Overwrite the port config to be the updated default port config dict
    port_config = default_port_config

    return port_config


def _get_settings_helper(configuration: dict) -> dict:
    vexbot = configuration.get('vexbot', {})
    vexbot_adapters = vexbot.get('vexbot_adapters', [])
    settings = {}
    for adapter in vexbot_adapters:
        adapter_settings = configuration.get(adapter)
        if adapter_setting is not None:
            settings[adapter] = adapter_settings

    return settings



def main(**kwargs):
    """
    `configuration_filepath`
    """
    # Get the command line arguments
    command_line_kwargs = _util.get_kwargs.get_kwargs()
    # Overwrite the function kwargs with the command line kwargs 
    kwargs.update(command_line_kwargs)

    # Get the configuration filepath
    config_filepath = kwargs.get('configuration_filepath')
    # Get the configuration (possibly the default configuration)
    configuration = _util.get_config.get_config(filepath=config_filepath)

    # setup some sane defaults
    default_vex_name = 'Vexbot'
    default_vexbot_settings = {'robot_name': default_vex_name}
    # Get the settings out of the configuration, falling back on the defaults
    vexbot_settings = configuration.get('vexbot', default_vexbot_settings)
    # Get the robot name out of the configuration, falling back on the default
    robot_name = vexbot_settings.get('robot_name', default_vex_name)

    # Get the port configuration
    port_config = _port_configuration_helper(configuration)

    messaging = Messaging(robot_name, kwargs=port_config)

    settings = _get_settings_helper(configuration)

    # create the settings manager using the port config
    settings_manager = _SettingsManager(configuration=port_configuration, settings=settings)
    adapter_interface = AdapterInterface(settings_manager,
                                         SubprocessManager())

    if _setproctitle:
        _setproctitle.setproctitle('vexbot')

    robot = Robot(messaging, adapter_interface)
    robot.run()


if __name__ == '__main__':
    main()
