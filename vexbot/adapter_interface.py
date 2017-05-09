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

        # Don't let the subprocess manager start the shell
        self.adapters = {}
        self.adapter_blacklist = ['shell', ]

    def get_settings_manager(self):
        return self.settings_manager

    def get_subprocess_manager(self):
        return self.subprocess_manager

    def get_adapters(self):
        return self.adapters.keys()

    def get_adapter_settings(self, name, profile):
        return self.settings_manager.get_adapter_settings(name)

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

    def start_adapters(self):
        pass

    def restart(self, name):
        pass

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

        for name, subprocess in subprocesses.items():
            if name in self.blacklist:
                continue

            self.adapters[name] = {'executable': sys.executable,
                                   'filepath': adapters.__file__}
                               
    def setup_settings(self):
        collect_epp = self.plugin_manager.collect_entry_point_plugins
        plugin_settings = collect_epp(('vexbot.adapter_settings',),
                                      return_dict=True,
                                      store_collected_plugins=False)

        self.settings_manager.settings.update(plugin_settings)
