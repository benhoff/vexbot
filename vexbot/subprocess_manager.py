import sys
import atexit
import signal
from subprocess import Popen, DEVNULL

from sqlalchemy import inspect as _sql_inspect
import sqlalchemy as _alchy
import sqlalchemy.orm as _orm

from vexbot.sql_helper import Base
from vexbot.robot_settings import RobotSettings


# This is going to work
# Couldn't tell you why though
class SubprocessDefaultSettings(Base):
    __tablename__ = 'subprocess_configuration'
    subprocess = _alchy.Column(_alchy.String(100))
    default_configuration = _alchy.Column(_alchy.String(100))
    robot_id = _alchy.Column(_alchy.Integer, _alchy.ForeignKey('robot.id'))
    robot_context = _orm.relationship(RobotSettings)


class SubprocessManager:
    def __init__(self, settings_manager=None):
        # this is going to be a list of filepaths
        self._registered = {}
        self._settings = {}
        # these will be subprocesses
        self._subprocess = {}
        atexit.register(self._close_subprocesses)
        signal.signal(signal.SIGINT, self._handle_close_signal)
        signal.signal(signal.SIGTERM, self._handle_close_signal)
        self.blacklist = ['shell', ]
        if settings_manager:
            self._handle_settings(settings_manager)

    def _handle_settings(self, manager):
        subprocess_settings = manager.get_subprocess_settings()
        for key, default in subprocess_settings.items():
            self._settings_configuration[key] = default

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

    def set_settings_class(self, name, kls):
        self._settings[name] = kls

    # FIXME: API broken
    def update_setting_value(self,
                             name: str,
                             setting_name: str,
                             setting_value):

        try:
            self._settings[name][setting_name] = setting_value
        except KeyError:
            pass

    def get_settings(self, key: str):
        """
        trys to get the settings information for a given subprocess. Passes
        silently when there is no information
        """
        settings = self._settings.get(key)
        return settings

    def _get_dict_from_settings(self, kls=None, configuration=None):
        result = {}
        if configuration is None or kls is None:
            return result

        for attribute in _sql_inspect(kls).attrs:
            key = attribute.key
            if not key in ('filepath', 'args'):
                key = '--' + key

            result[attribute.key] = attribute.value

        return result


    def start(self, keys: list):
        """
        starts subprocesses. Can pass in multiple subprocess to start
        """
        for key in keys:
            executable = self._registered.get(key)
            if executable is None:
                continue

            dict_list = [executable, ]
            default_configuration = self._settings_configuration.get(key)
            settings_class = self._settings.get(key)
            settings = self._get_dict_from_settings(settings_class,
                                                    default_configuration)

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
