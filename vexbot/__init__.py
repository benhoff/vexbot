from vexbot._version import __version__ # flake8: noqa


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


def _get_adapter_settings_helper(configuration: dict) -> dict:
    vexbot = configuration.get('vexbot', {})
    vexbot_adapters = vexbot.get('vexbot_adapters', [])
    settings = {}
    for adapter in vexbot_adapters:
        adapter_settings = configuration.get(adapter)
        if adapter_setting is not None:
            settings[adapter] = adapter_settings

    return settings
