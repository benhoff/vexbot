import sys
import atexit
import signal
import logging

from pydbus import SessionBus

import pluginmanager


class SubprocessManager:
    def __init__(self):
        self.bus = SessionBus()
        self.systemd = self.bus.get('.systemd1')

        # atexit.register(self._close_subprocesses)
        # signal.signal(signal.SIGINT, self._handle_close_signal)
        # signal.signal(signal.SIGTERM, self._handle_close_signal)

    def start(self, name: str, mode: str='replace'):
        self.systemd.StartUnit(name, mode)

    def restart(self, name: str, mode: str='replace'):
        self.systemd.ReloadOrRestart(name, mode)

    def stop(self, name: str, mode: str='replace'):
        self.systemd.StopUnit(name, mode)

    """
    def mask(self, name: str):
        pass

    def unmask(self, name: str):
        pass
    """

    def killall(self):
        """
        Kills every registered subprocess
        """
        pass

    def _handle_close_signal(self, signum=None, frame=None):
        # self._close_subprocesses()
        # sys.exit()
        pass

    def _close_subprocesses(self):
        """
        signum and frame are part of the signal lib
        """
        pass
