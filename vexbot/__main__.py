#!/usr/bin/env python3

# import atexit

try:
    import setproctitle as _setproctitle
except ImportError:
    _setproctitle = False

from vexbot import _port_configuration_helper, _get_adapter_settings_helper

# from vexbot.commands.start_vexbot import start_vexbot
# from vexbot.adapters.shell.__main__ import main as shell_main

from vexbot.robot import Robot
from vexbot.util import get_kwargs as _get_kwargs
from vexbot.util import get_config as _get_config

from vexbot.messaging import Messaging as _Messaging
from vexbot.settings_manager import SettingsManager as _SettingsManager
from vexbot.subprocess_manager import SubprocessManager as _SubprocessManager


def _update_kwargs_with_command_line_arguments(**kwargs):
    command_line_kwargs = _get_kwargs.get_kwargs()
    kwargs.update(command_line_kwargs)
    return kwargs


def _get_configuration_from_file(**kwargs):
    config_filepath = kwargs.get('configuration_filepath')
    configuration = _get_config.get_config(filepath=config_filepath)
    return configuration


def _configuration_sane_defaults(configuration: dict) -> (dict, str):
    default_vex_name = 'Vexbot'
    default_vexbot_settings = {'robot_name': default_vex_name}
    # Get the settings out of the configuration, falling back on the defaults
    vexbot_settings = configuration.get('vexbot', default_vexbot_settings)
    # Get the robot name out of the configuration, falling back on the default
    robot_name = vexbot_settings.get('robot_name', default_vex_name)

    return vexbot_settings, robot_name


def main(*args, **kwargs):
    """
    `kwargs`:

        `configuration_filepath`: filepath for the `ini` configuration
    """
    # Update kwargs with command line arguments
    kwargs = _update_kwargs_with_command_line_arguments(kwargs=kwargs)

    # configuration is from an `ini` file
    # NOTE: we are done with kwargs from this point on.
    configuration = _get_configuration_from_file(kwargs=kwargs)

    # setup some sane defaults
    # FIXME: `vexbot_settings` not used
    _, robot_name = _configuration_sane_defaults(configuration)

    # Get the port configuration out of the configuration
    port_config = _port_configuration_helper(configuration)

    # create the messaging
    messaging = _Messaging(robot_name, kwargs=port_config)
    # get the adapter settings
    adapter_settings = _get_adapter_settings_helper(configuration)

    # TODO: Fix the SettingsManager API. Confusing
    settings_manager = _SettingsManager(configuration=port_config,
                                        settings=adapter_settings)

    # create the settings manager using the port config
    if _setproctitle:
        _setproctitle.setproctitle('vexbot')

    robot = Robot(messaging)
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
    main(**debug)
