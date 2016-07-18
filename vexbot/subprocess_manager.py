import sys
import atexit
import signal
from subprocess import Popen, DEVNULL


class SubprocessManager:
    def __init__(self):
        # this is going to be a list of filepaths
        self._registered = {}
        self._settings = {}
        # these will be subprocesses
        self._subprocess = {}
        atexit.register(self._close_subprocesses)
        signal.signal(signal.SIGINT, self._handle_close_signal)
        signal.signal(signal.SIGTERM, self._handle_close_signal)
        self.blacklist = ['shell', ]

    def _handle_close_signal(self, signum=None, frame=None):
        self._close_subprocesses()
        sys.exit()

    def _close_subprocesses(self):
        """
        signum and frame are part of the signal lib
        """
        for process in self._subprocess.values():
            process.terminate()

    def registered_subprocesses(self):
        """
        returns all possible subprocesses that can be launched
        """
        return tuple(self._registered.keys())

    def register(self, key: str, value, settings: dict=None):
        self._settings[key] = settings
        if key in self.blacklist:
            return
        self._registered[key] = value

    def update_setting_value(self,
                             name: str,
                             setting_name: str,
                             setting_value):

        try:
            self._settings[name][setting_name] = setting_value
        except KeyError:
            pass

    def update_settings(self, name: str, settings: dict):
        """
        Need to pass in the subprocess name, a setting to be changed,
        and the value to change the setting to
        """
        old_settings = self._settings.get(name)
        if old_settings:
            old_settings.update(settings)
        else:
            self._settings[name] = settings

    def get_settings(self, key: str):
        """
        trys to get the settings information for a given subprocess. Passes
        silently when there is no information
        """
        settings = self._settings.get(key)
        return settings

    def start(self, keys: list):
        """
        starts subprocesses. Can pass in multiple subprocess to start
        """
        for key in keys:
            executable = self._registered.get(key)
            if executable is None:
                continue

            dict_list = [executable, ]
            settings = self._settings.get(key, {})
            filepath = settings.get('filepath')
            if filepath:
                dict_list.append(filepath)

            args = settings.get('args', [])
            if args:
                dict_list.extend(args)

            for k, v in settings.items():
                if k == 'filepath':
                    continue
                dict_list.append(k)
                dict_list.append(v)

            process = Popen(dict_list, stdout=DEVNULL)
            return_code = process.poll()
            if return_code is None:
                self._subprocess[key] = process

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

    def terminate(self, values: list):
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
