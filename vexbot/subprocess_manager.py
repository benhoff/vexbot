import sys
import atexit
import signal
import logging
# TODO: Determine if there's a better way to import this
from gi._error import GError

from pydbus import SessionBus, SystemBus

import pluginmanager


class SubprocessManager:
    def __init__(self):
        self.session_bus_available = True
        try:
            self.bus = SessionBus()
        except GError:
            # NOTE: no session bus if we're here.
            self.session_bus_available = False
            self.system_bus = SystemBus()

        # TODO: Verify that we can start services as the system bus w/o root
        # permissions
        if self.session_bus_available:
            self.systemd = self.bus.get('.systemd1')
        else:
            self.systemd = self.system_bus.get('.systemd1')

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
