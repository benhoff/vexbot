import sys
import atexit
import signal
import logging
from subprocess import Popen, DEVNULL

import pluginmanager


class SubprocessManager:
    def __init__(self):
        # Don't let the subprocess manager start the shell
        self.blacklist = ['shell', ]
        self._registered = {}
        self._subprocess = {}

        atexit.register(self._close_subprocesses)
        signal.signal(signal.SIGINT, self._handle_close_signal)
        signal.signal(signal.SIGTERM, self._handle_close_signal)

    def register_subprocesses(self, entry_point='vexbot.subprocesses'):
        plugin_manager = pluginmanager.PluginInterface()
        subprocesses = collect_ep((entry_point,), return_dict=True)
        for name, subprocess in subprocesses.items():
            if name in self.blacklist:
                continue

            self._registered[name] = {'executable': sys.executable,
                                      'filepath': subprocess.__file__}

    def registered_subprocesses(self):
        """
        returns all possible subprocesses that can be launched
        """
        return tuple(self._registered.keys())

    """
    # This is what we're aiming for.
        process = Popen(dict_list, stdout=DEVNULL)
        return_code = process.poll()
        if return_code is None:
            self._subprocess[key] = process
    """
    def start(self, keys: list, settings: list):
        # Cover the case where there are no settings passed in
        if settings is None:
            settings = []
        # iterate through each of the keys and the settings
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


    def restart(self, values: list):
        """
        restarts subprocesses managed by the subprocess manager
        """
        for value in values:
            try:
                process = self._subprocess[value]
            except KeyError:
                continue

            process.terminate()
            self.start((value, ))

    def kill(self, values: list):
        """
        kills subprocess that is managed by the subprocess manager.
        If value does not match, quietly passes for now
        """
        for value in values:
            try:
                process = self._subprocess[value]
            except KeyError:
                continue
            process.kill()

    def stop(self, values: list):
        for value in values:
            try:
                process = self._subprocess[value]
            except KeyError:
                continue
            process.terminate()

    def killall(self):
        """
        Kills every registered subprocess
        """
        for subprocess in self._subprocess.values():
            subprocess.kill()

    def running_subprocesses(self):
        """
        returns all running subprocess names
        """
        results = []
        killed = []
        for name, subprocess in self._subprocess.items():
            poll = subprocess.poll()
            if poll is None:
                results.append(name)
            else:
                killed.append(name)
        if killed:
            for killed_subprocess in killed:
                self._subprocess.pop(killed_subprocess)
        return results

    def _handle_close_signal(self, signum=None, frame=None):
        self._close_subprocesses()
        sys.exit()

    def _close_subprocesses(self):
        """
        signum and frame are part of the signal lib
        """
        for process in self._subprocess.values():
            process.terminate()

