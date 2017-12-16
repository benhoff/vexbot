from abc import ABCMeta as _ABCMeta
from abc import abstractmethod as _abstractmethod
from vexbot.extensions import extendmany as _extendmany


class Observer(metaclass=_ABCMeta):
    extensions = ()
    def __init__(self, *args, **kwargs):
        # FIXME: Hack
        _extendmany(self.__class__, *self.extensions)

    @_abstractmethod
    def on_next(self, value):
        return NotImplemented

    @_abstractmethod
    def on_error(self, error):
        return NotImplemented

    @_abstractmethod
    def on_completed(self):
        return NotImplemented

    def extend(self, method, alias: list=None, name: str=None, hidden: bool=False):
        if name is None:
            name = method.__name__
        method.hidden = hidden
        self._commands[name] = method
        if alias:
            # TODO: Throw error if we're overwriting a name
            for a in alias:
                self._commands[a] = method

    def extendmany(self, *methods):
        for method in methods:
            self.extend(method)
