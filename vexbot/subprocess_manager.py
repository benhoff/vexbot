import sys
import atexit
import signal
import logging
from subprocess import Popen, DEVNULL

import pluginmanager


class SubprocessManager:
    def __init__(self):
        self._subprocess = {}

        atexit.register(self._close_subprocesses)
        signal.signal(signal.SIGINT, self._handle_close_signal)
        signal.signal(signal.SIGTERM, self._handle_close_signal)

    def start(self, name: str, arguments: list):
        process = Popen(arguments, stdout=DEVNULL)
        return_code = process.poll()
        # TODO: Check and return error code
        if return_code is None:
            self._subprocess[name] = process

    def restart(self, name: str, arguments: list):
        """
        restarts subprocesses managed by the subprocess manager
        """
        try:
            process = self._subprocess[name]
        except KeyError:
            continue

            process.terminate()

        self.start(name, arguments)

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
