#!/usr/bin/env python3

# import atexit

try:
    import setproctitle as _setproctitle
except ImportError:
    _setproctitle = False

from vexbot import _port_configuration_helper

from vexbot.robot import Robot
from vexbot.util.get_config_filepath import get_config_filepath
from vexbot.util.get_kwargs import get_kwargs as _get_kwargs
from vexbot.util.get_config import get_config as _get_config


def _get_bot_name_gracefully(configuration: dict) -> str:
    """
    Parses the bot name out of the expected configuration format, failing
    gracefully to the default of `vexbot` at every turn.

    Args:
        configuration (dict): Dict representing the expected file format of
        {'vexbot': {'bot_name': 'CUSTOM_NAME_HERE'}}

    Returns:
        str: the custom name, or `vexbot` if parsing fails.
    """
    default_vexbot_settings = {'bot_name': 'vexbot'}
    # Get the settings out of the configuration, falling back on the defaults
    vexbot_settings = configuration.get('vexbot', default_vexbot_settings)
    # Get the robot name out of the configuration, falling back on the default
    robot_name = vexbot_settings.get('bot_name', 'vexbot')

    return robot_name


def main(*args, configuration_filepath: str=None, **kwargs) -> None:
    """
    Run the robot, using both the command line arguments and the configuration
    file.

    Args:
        configuration_filepath (str): Optional overide for the vexbot
        configuration filepath
    """
    kwargs = {**kwargs, **_get_kwargs()}
    if configuration_filepath is None:
        configuration_filepath = get_config_filepath()

    # configuration is from an `ini` file and parsed using `ConfigParser`
    configuration = _get_config(configuration_filepath)

    # Get the bot name out, smoothly
    robot_name = _get_bot_name_gracefully(configuration)

    # Get the port configuration out of the configuration
    port_config = _port_configuration_helper(configuration)

    # create the settings manager using the port config
    if _setproctitle:
        _setproctitle.setproctitle('vexbot')

    robot = Robot(robot_name, port_config)
    # NOTE: Blocking call
    robot.run()


if __name__ == "__main__":
    main()
