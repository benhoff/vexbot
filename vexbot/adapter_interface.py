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
        self.setup_adapters()

    def get_settings_manager(self):
        return self.settings_manager

    def get_subprocess_manager(self):
        return self.subprocess_manager

    def get_adapters(self):
        return self.adapters.keys()

    def start_profile(self, profile='default'):
        settings = self.settings_manager.get_adapter_settings(profile)
        for name, adapter_settings in settings.items():
            adapter = self.adapters.get(name)
            if adapter is None:
                continue
            new_settings = []
            new_settings.append(adapter['executable'])
            new_settings.append(adapter['filepath'])

            for k, v in adapter_settings:
                new_settings.append('--' + k)
                new_settings.append(v)
            self.subprocess_manager.start(name, new_settings)


    def start_adapter(self):
        pass
        """
        for key, setting in zip(keys, settings):
            if registered_dict is None:
                continue

            dict_list = [executable, ]
            settings = self._settings.get(key)

            settings_class = settings.get('settings_class')
            setting_values = {}

            filepath = settings.get('filepath')
            if filepath:
                dict_list.append(filepath)

            args = settings.get('args', [])
            if args:
                dict_list.extend(args)

            # Not sure if this will work
            settings.update(setting_values)

            for k, v in settings.items():
                if k in ('filepath', '_sa_instance_state', 'id', 'robot_id'):
                    continue
                if not k[2:] == '--':
                    k = '--' + k
                dict_list.append(k)
                dict_list.append(v)
        """

    def kill(self, names: list):
        self.subprocess_manager.kill(names)

    def killall(self):
        self.subprocess_manager.killall()

    def setup(self,
              settings_entry_point='vexbot.adapter_settings',
              adapter_entry_point='vexbot.subprocesses'):

        self._setup_adapters(settings_entry_point)
        self._setup_settings(adapter_entry_point)

    def setup_adapters(self, entry_point='vexbot.subprocesses'):
        collect_epp = self.plugin_manager.collect_entry_point_plugins
        adapters = collect_epp((entry_point,),
                               return_dict=True,
                               store_collected_plugins=False)

        for name, subprocess in adapters.items():
            if name in self.adapter_blacklist:
                continue

            self.adapters[name] = {'executable': sys.executable,
                                   'filepath': subprocess.__file__}
