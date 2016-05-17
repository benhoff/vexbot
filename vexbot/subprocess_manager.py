import sys
import atexit
from subprocess import Popen, DEVNULL, STDOUT


class SubprocessManager:
    def __init__(self):
        # this is going to be a list of filepaths
        self._registered = {}
        # these will be subprocesses
        self._subprocess = {}
        atexit.register(self._close_subprocesses)

    def _close_subprocesses(self):
        for process in self._subprocess.values():
            process.terminate()

    def register(self, keys, values, settings=None):
        if settings is None:
            settings = [None for _ in range(len(keys))]

        for key, value, setting in zip(keys, values, settings):
            self._registered[key] = (value, setting)

    def update(self, key, value=None, setting=None):
        """
        This allows us to update the settings or value
        """
        if setting is None:
            settings = self._registered[key][1]
        if value is None:
            value = self._registered[key][0]
        self._registered[key] = (value, setting)

    def start(self, keys):
        for key in keys:
            try:
                data = self._registered[key]
            except KeyError:
                data = None

            if data:
                args = [sys.executable, data[0]]
                if data[1]:
                    args.extend(data[1])
                process = Popen(args, stdout=DEVNULL, stderr=STDOUT)
                self._subprocess[key] = process

    def restart(self, values):
        for value in values:
            process = self._subprocess[value]
            process.kill()
            self.start(value)

    def kill(self, values):
        for value in values:
            process = self._subprocess[value]
            process.kill()

    def killall(self):
        for subprocess in self._subprocess.values():
            subprocess.kill()
