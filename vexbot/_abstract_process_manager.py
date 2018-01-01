from abc import ABCMeta as _ABCMeta
from abc import abstractmethod as _abstractmethod


class AbstractProcessManager(metaclass=_ABCMeta):
    """
    Documents the required methods to implement a non-DBus process manager
    """

    @_abstractmethod
    def start(self, name: str, mode: str='replace'):
        """
        Args:
            name (str): likely to end in `.service` or `.target`. I.e,
            `vexbot.service`.
            mode (str): to be one of replace, fail, isolate, 
                ignore-dependencies, ignore-requirements
        """
        pass

    @_abstractmethod
    def restart(self, name: str, mode: str='replace'):
        """
        Args:
            name (str): likely to end in `.service` or `.target`. I.e,
            `vexbot.service`.
            mode (str): to be one of replace, fail, isolate, 
                ignore-dependencies, ignore-requirements
        """
        pass

    @_abstractmethod
    def stop(self, name: str, mode: str='replace'):
        """
        Args:
            name (str): likely to end in `.service` or `.target`. I.e,
            `vexbot.service`.
            mode (str): to be one of replace, fail, isolate, 
                ignore-dependencies, ignore-requirements
        """
        pass

    @_abstractmethod
    def uptime(self, name: str) -> str:
        """
        Args:
            name (str): likely to end in `.service` or `.target`. I.e,
            `vexbot.service`.

        Returns:
            str: the uptime
        """
        pass

    @_abstractmethod
    def status(self, name: str) -> str:
        """
        Args:
            name (str): likely to end in `.service` or `.target`. I.e,
            `vexbot.service`.

        Returns:
            str: the status of the program
        """
        pass
