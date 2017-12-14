from abc import ABCMeta, abstractmethod
from vexbot.extension import extend


class Observer(metaclass=ABCMeta):
    extensions = ()
    def __init__(self, *args, **kwargs):
        for extension in self.extensions:
            # FIXME: Hack
            extend(self.__class__, extension)

    @abstractmethod
    def on_next(self, value):
        return NotImplemented

    @abstractmethod
    def on_error(self, error):
        return NotImplemented

    @abstractmethod
    def on_completed(self):
        return NotImplemented
