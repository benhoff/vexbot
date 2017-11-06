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


def _configuration_sane_defaults(configuration: dict) -> (dict, str):
    default_vexbot_settings = {'bot_name': 'vexbot'}
    # Get the settings out of the configuration, falling back on the defaults
    vexbot_settings = configuration.get('vexbot', default_vexbot_settings)
    # Get the robot name out of the configuration, falling back on the default
    robot_name = vexbot_settings.get('bot_name', 'vexbot')

    return robot_name


def main(*args, **kwargs):
    """
    `kwargs`:

        `configuration_filepath`: filepath for the `ini` configuration
    """
    kwargs = {**kwargs, **_get_kwargs()}
    # FIXME: This filepath handeling is messed up and not transparent as it should be
    default_filepath = get_config_filepath()
    configuration_filepath = kwargs.get('configuration_filepath')
    if configuration_filepath is None:
        configuration_filepath = default_filepath
    # configuration is from an `ini` file
    configuration = _get_config(configuration_filepath)
    # setup some sane defaults
    robot_name = _configuration_sane_defaults(configuration)
    # Get the port configuration out of the configuration
    port_config = _port_configuration_helper(configuration)
    # create the settings manager using the port config
    if _setproctitle:
        _setproctitle.setproctitle('vexbot')

    robot = Robot(robot_name, port_config)
    robot.run()


if __name__ == "__main__":
    main()
