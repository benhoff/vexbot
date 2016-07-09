import sys
import atexit
import signal
from subprocess import Popen, DEVNULL


class SubprocessManager:
    def __init__(self):
        # this is going to be a list of filepaths
        self._registered = {}
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

    def register(self, keys, values, settings=None):
        if settings is None:
            settings = [None for _ in range(len(keys))]

        for key, value, setting in zip(keys, values, settings):
            if key in self.blacklist:
                continue

            self._registered[key] = (value, setting)

    def update(self, key, value=None, setting=None):
        """
        This allows us to update the settings or value
        """
        if key in self.blacklist:
            return

        if setting is None:
            setting = self._registered[key][1]
        if value is None:
            value = self._registered[key][0]
        self._registered[key] = (value, setting)

    def settings(self, key):
        """
        trys to get the settings information for a given subprocess. Passes
        silently when there is no information
        """
        if not key:
            return
        # FIXME
        try:
            v = self._registered.get(key, None)
        except TypeError:
            # FIXME
            v = self._registered.get(key[0])
        if v:
            return v[1]

    def start(self, keys):
        """
        starts subprocesses. Can pass in multiple subprocess to start
        """
        for key in keys:
            try:
                data = self._registered[key]
            except KeyError:
                data = None

            if data:
                args = [sys.executable, data[0]]
                if data[1]:
                    args.extend(data[1])
                process = Popen(args, stdout=DEVNULL)
                self._subprocess[key] = process

    def restart(self, values):
        """
        restarts subprocesses managed by the subprocess manager
        """
        for value in values:
            try:
                process = self._subprocess[value]
            except KeyError:
                continue

            process.kill()
            self.start(value)

    def kill(self, values):
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
            self._subprocess.pop(value)

    def killall(self):
        """
        Kills every registered subprocess
        """
        for subprocess in self._subprocess.values():
            subprocess.kill()

        self._subprocess = {}

    def running_subprocesses(self):
        """
        returns all running subprocess names
        """
        return tuple(self._subprocess.keys())
