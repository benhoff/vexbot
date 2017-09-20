# import atexit
# import signal

# TODO: Determine if there's a better way to import this
from gi._error import GError as _GError

from pydbus import SessionBus as _SessionBus
from pydbus import SystemBus as _SystemBus


# TODO: think of a better name
class SubprocessManager:
    def __init__(self):
        self.session_bus_available = True
        try:
            self.bus = _SessionBus()
        except _GError:
            # No session bus if we're here. Depending on linux distro, that's
            # not surprising
            self.session_bus_available = False

        # TODO: It's possible that the user is on a system that is not using
        # systemd, which means that this next call will fail. Should probably
        # have a try/catch and then just default to not having a subprocess
        # manager if that happens.
        self.system_bus = _SystemBus()

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

    def killall(self):
        pass
    """
