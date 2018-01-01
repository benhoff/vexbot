import logging
from vexbot._version import __version__ # flake8: noqa

# FIXME: probably don't want to add NullHandler here
# NOTE: This is here to prevent the default handler being added upon init of the program
logging.getLogger(__name__).addHandler(logging.NullHandler())


def _port_configuration_helper(configuration: dict) -> dict:
    """
    Helper method to get the Zmq Address information out of the vexbot
    configuration file. Get's the default port configuration info and then
    updates the default configuration information from the config file.
    Ensures that there are some values if our configuration is missing some.

    Args:
        configuration (dict): Values of the config file. Should have
            {'connection': {}}, but will fall back gracefully if this is not
            the case
    Returns:
        dict: port configuration information.
    """
    default_port_config = _get_default_port_config()

    # get the port settings out of the configuration, falling back on defaults
    # NOTE: Should probably warn here if we don't find anything
    port_config = configuration.get('connection', default_port_config)

    # update the defaults with the retrived port configs
    default_port_config.update(port_config)
    # Overwrite the port config to be the updated default port config dict
    port_config = default_port_config

    return port_config


# TODO: Rename this to be `_get_default_robot_port_config` or similar
def _get_default_port_config() -> dict:
    """
    Gets/sets default Zmq address information for a locally run bot.

    Returns:
        dict: The default robot messaging configuration. Note that this binds
            to all adapters
            {protocol: 'tcp',
             address: '*',
             chatter_publish_port: 4000,
             chatter_subscription_port: [4001,],
             command_port: 4002,
             request_port: 4003,
             control_port: 4005}
    """
    # Setup some default port configurations
    default_port_config= {'protocol': 'tcp',
                          'address': '*',
                          'chatter_publish_port': 4000,
                          # FIXME: There's probably not a good reason to have
                          # this be an iterable
                          'chatter_subscription_port': [4001,],
                          'request_port': 4003,
                          'command_port': 4004,
                          'control_port': 4005}

    return default_port_config


def _get_default_adapter_config() -> dict:
    """
    Get/set's the default Zmq adapter address information for a locally run
    bot.

    Returns:
        dict: The default adapter config for a locally run helper
            {protocol: 'tcp',
             address: '127.0.0.1',
             chatter_publish_port: 4000,
             chatter_subscription_port: [4001,],
             command_port: 4002,
             request_port: 4003,
             control_port: 4005}
    """
    config = _get_default_port_config()
    config['address'] = '127.0.0.1'
    return config
