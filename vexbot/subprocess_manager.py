import time as _time
# import atexit
# import signal

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


def _pretty_time_delta(seconds):
    seconds = abs(int(seconds))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return '%dday %dh' % (days, hours)
    elif hours > 0:
        return '%dh %dmin' % (hours, minutes)
    elif minutes > 0:
        return '%dmin %dsec' % (minutes, seconds)
    else:
        return '{}s'.format(seconds)


# TODO: think of a better name
class SubprocessManager:
    def __init__(self):
        self.session_bus_available = True
        try:
            self.bus = _SessionBus()
        # NOTE: GError from package `gi`
        except Exception:
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

    def start(self, name: str, mode: str='replace') -> None:
        # TODO: add in some parsing if fail
        # https://github.com/LEW21/pydbus/issues/35
        name = _name_helper(name)
        self.systemd.StartUnit(name, mode)

    def restart(self, name: str, mode: str='replace') -> None:
        name = _name_helper(name)
        self.systemd.ReloadOrRestartUnit(name, mode)

    def stop(self, name: str, mode: str='replace') -> None:
        name = _name_helper(name)
        self.systemd.StopUnit(name, mode)

    def _uptime(self, unit):
        time_start = unit.ConditionTimestamp/1000000
        delta = _time.time() - time_start
        delta = _pretty_time_delta(delta)
        return delta

    def uptime(self, name: str) -> str:
        unit = self.bus.get('.systemd1', self.systemd.GetUnit(name))
        return self._uptime(unit) 

    def status(self, name: str) -> str:
        name = _name_helper(name)
        unit = self.bus.get('.systemd1', self.systemd.GetUnit(name))
        # NOTE: what systemctl status shows
        # freenode.service - IRC Client
        # active (running) since Tue 2017-10-17 10:36:03 UTC; 19s ago
        delta = self._uptime(unit)
        fo = '%a %b %d %H:%M:%S %Y'
        time_start = time_start = unit.ConditionTimestamp/1000000 
        time_stamp = _time.strftime(fo, _time.gmtime(time_start))
        return '{}: {} ({}) since {}; {} ago'.format(unit.Id,
                                                     unit.ActiveState,
                                                     unit.SubState,
                                                     time_stamp,
                                                     delta)

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
