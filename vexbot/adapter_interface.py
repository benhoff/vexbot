import sys

import pluginmanager


class AdapterInterface:
    def __init__(self,
                 settings_manager: 'vexbot.SettingsManager'=None,
                 subprocess_manager: 'vexbot.SubprocessManager'=None,
                 plugin_manager: 'pluginmanager.PluginInterface'=None):

        self.settings_manager = settings_manager
        self.subprocess_manager = subprocess_manager

        if plugin_manager is None:
            plugin_manager = pluginmanager.PluginInterface()

        self.plugin_manager = plugin_manager

        self.adapters = {}
        self.adapter_blacklist = []
        self.setup()

    def get_settings_manager(self):
        return self.settings_manager

    def get_subprocess_manager(self):
        return self.subprocess_manager

    def get_adapters(self):
        return self.adapters.keys()

    def start_profile(self, profile: str='default') -> None:
        settings = self.settings_manager.get_adapter_settings(profile)
        for name, adapter_settings in settings.items():
            adapter = self.adapters.get(name)
            if adapter is None:
                continue
            new_settings = []
            new_settings.append(adapter['executable'])
            new_settings.append(adapter['filepath'])

            # TODO: add in ability to pass in args?
            for k, v in adapter_settings:
                new_settings.append('--' + k)
                new_settings.append(v)

            self.subprocess_manager.start(name, new_settings)

    def start_adapter(self, name, filter_, value):
        pass

    def kill(self, names: list):
        self.subprocess_manager.kill(names)

    def killall(self):
        self.subprocess_manager.killall()

    def setup(self, entry_point='vexbot.subprocesses'):
        collect_epp = self.plugin_manager.collect_entry_point_plugins
        adapters = collect_epp((entry_point,),
                               return_dict=True,
                               store_collected_plugins=False)

        for name, subprocess in adapters.items():
            if name in self.adapter_blacklist:
                continue

            # TODO: Add option to start with something other than python interp
            self.adapters[name] = {'executable': sys.executable,
                                   'filepath': subprocess.__file__}
