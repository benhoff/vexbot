# import atexit
# import signal

# TODO: Determine if there's a better way to import this
from gi._error import GError as _GError

from pydbus import SessionBus as _SessionBus
from pydbus import SystemBus as _SystemBus


def _name_helper(name: str):
    """
    default to returning a name with `.service`
    """
    name = name.rstrip()
    if name.endswith(('.service', '.socket', '.target')):
        return name
    return name + '.service'


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
        # TODO: add in some parsing if fail
        # https://github.com/LEW21/pydbus/issues/35
        name = _name_helper(name)
        self.systemd.StartUnit(name, mode)

    def restart(self, name: str, mode: str='replace'):
        name = _name_helper(name)
        self.systemd.ReloadOrRestartUnit(name, mode)

    def stop(self, name: str, mode: str='replace'):
        name = _name_helper(name)
        self.systemd.StopUnit(name, mode)

    def status(self, name: str):
        name = _name_helper(name)
        unit = self.bus.get('.systemd1', self.systemd.GetUnit(name))
        # NOTE: what systemctl status shows
        # irc.service - IRC Client
        # active (running) since Tue 2017-10-17 10:36:03 UTC; 19s ago
        return '{}: {} ({})'.format(unit.Id, unit.ActiveState, unit.SubState)

    def get_units(self):
        return self.systemd.ListUnits()

    """
    def mask(self, name: str):
        pass

    def unmask(self, name: str):
        pass

    def killall(self):
        pass
    """
