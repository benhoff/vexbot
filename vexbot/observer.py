from abc import ABCMeta as _ABCMeta
from abc import abstractmethod as _abstractmethod
from vexbot.extensions import extend as _extend


class Observer(metaclass=_ABCMeta):
    extensions = ()
    def __init__(self, *args, **kwargs):
        for extension in self.extensions:
            # FIXME: Hack
            _extend(self.__class__, extension)

    @_abstractmethod
    def on_next(self, value):
        return NotImplemented

    @_abstractmethod
    def on_error(self, error):
        return NotImplemented

    @_abstractmethod
    def on_completed(self):
        return NotImplemented
