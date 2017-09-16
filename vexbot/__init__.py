from vexbot._version import __version__ # flake8: noqa


def _port_configuration_helper(configuration: dict) -> dict:
    default_port_config = _get_default_port_config()

    # get the port settings out of the configuration, falling back on defaults
    port_config = configuration.get('vexbot_ports', default_port_config)

    # update the defaults with the retrived port configs
    default_port_config.update(port_config)
    # Overwrite the port config to be the updated default port config dict
    port_config = default_port_config

    return port_config

def _get_default_port_config():
    """
    protocol:   'ipc'
    ip_address: '127.0.0.1'
    chatter_publish_port: 4000
    chatter_subscription_port: [4001,]
    command_port: 4002
    request_port: 4003
    control_port: 4005
    """
    # Setup some default port configurations
    default_port_config= {'protocol': 'ipc',
                          'ip_address': '127.0.0.1',
                          'chatter_publish_port': 4000,
                          'chatter_subscription_port': [4001,],
                          'request_port': 4003,
                          'command_port': 4004,
                          'control_port': 4005}

    return default_port_config

def _get_adapter_settings_helper(configuration: dict) -> dict:
    vexbot = configuration.get('vexbot', {})
    vexbot_adapters = vexbot.get('vexbot_adapters', [])
    settings = {}
    for adapter in vexbot_adapters:
        adapter_settings = configuration.get(adapter)
        if adapter_setting is not None:
            settings[adapter] = adapter_settings

    return settings
