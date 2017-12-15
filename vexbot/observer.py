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
