#!/usr/bin/env python3

# import atexit

try:
    import setproctitle as _setproctitle
except ImportError:
    _setproctitle = False

from vexbot import _port_configuration_helper, _get_settings_helper

# from vexbot.commands.start_vexbot import start_vexbot
# from vexbot.adapters.shell.__main__ import main as shell_main

from vexbot.robot import Robot
from vexbot.util import get_kwargs as _get_kwargs
from vexbot.util import get_config as _get_config

from vexbot.messaging import Messaging as _Messaging
from vexbot.settings_manager import SettingsManager as _SettingsManager
from vexbot.subprocess_manager import SubprocessManager as _SubprocessManager
from vexbot.adapter_interface import AdapterInterface as _AdapterInterface


def _create_settings_manager(port_configuration: dict,
                             settings: dict) -> _SettingsManager:

    settings_manager = _SettingsManager(configuration=port_configuration,
                                        settings=settings)

    return settings_manager


def _update_with_command_line_arguments(**kwargs):
    command_line_kwargs = _get_kwargs.get_kwargs()
    kwargs.update(command_line_kwargs)
    return kwargs


def _get_configuration(**settings):
    config_filepath = settings.get('configuration_filepath')
    configuration = _get_config.get_config(filepath=config_filepath)
    return configuration


def _sane_defaults(configuration: dict) -> (dict, str):
    default_vex_name = 'Vexbot'
    default_vexbot_settings = {'robot_name': default_vex_name}
    # Get the settings out of the configuration, falling back on the defaults
    vexbot_settings = configuration.get('vexbot', default_vexbot_settings)
    # Get the robot name out of the configuration, falling back on the default
    robot_name = vexbot_settings.get('robot_name', default_vex_name)

    return vexbot_settings, robot_name


def main(*args, **kwargs):
    """
    `configuration_filepath`
    """
    kwargs = _update_with_command_line_arguments(kwargs=kwargs)
    configuration = _get_configuration(settings=kwargs)

    # setup some sane defaults
    vexbot_settings, robot_name = _sane_defaults(configuration)

    # Get the port configuration
    port_config = _port_configuration_helper(configuration)

    messaging = _Messaging(robot_name, kwargs=port_config)
    settings = _get_settings_helper(configuration)
    # TODO: Fix this api. Confusing
    settings_manager = _create_settings_manager(port_config,
                                                settings)

    # create the settings manager using the port config

    adapter_interface = _AdapterInterface(settings_manager,
                                          _SubprocessManager())

    if _setproctitle:
        _setproctitle.setproctitle('vexbot')

    robot = Robot(messaging, adapter_interface)
    robot.run()


"""
def _kill_vexbot(process):
    def inner():
        process.terminate()

    return inner


def main(**settings):
    process = start_vexbot()
    if process and settings.get('kill_on_exit', False):
        atexit.register(_kill_vexbot(process))

    shell_settings = settings.get('shell', {})
    # Launch the shell interface
    shell_main(**shell_settings)
"""

if __name__ == "__main__":
    debug = {'kill_on_exit': True}
    """
    if _setproctitle:
        _setproctitle.setproctitle('vexshell')
    """

    main(**debug)
