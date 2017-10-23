#!/usr/bin/env python3

# import atexit

try:
    import setproctitle as _setproctitle
except ImportError:
    _setproctitle = False

from vexbot import _port_configuration_helper, _get_adapter_settings_helper

from vexbot.robot import Robot
from vexbot.util.get_kwargs import get_kwargs as _get_kwargs
from vexbot.util.get_config import get_config as _get_config

from vexbot.messaging import Messaging as _Messaging


def _configuration_sane_defaults(configuration: dict) -> (dict, str):
    default_vex_name = 'vexbot'
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
    kwargs = {**kwargs, **_get_kwargs()}
    # configuration is from an `ini` file
    configuration = _get_config(kwargs.get('configuration_filepath')
    # setup some sane defaults
    _, robot_name = _configuration_sane_defaults(configuration)
    # Get the port configuration out of the configuration
    port_config = _port_configuration_helper(configuration)
    # create the messaging
    messaging = _Messaging(robot_name, **port_config)
    # get the adapter settings
    adapter_settings = _get_adapter_settings_helper(configuration)

    # create the settings manager using the port config
    if _setproctitle:
        _setproctitle.setproctitle('vexbot')

    robot = Robot(messaging)
    robot.run()


if __name__ == "__main__":
    main()
