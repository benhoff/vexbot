from abc import ABCMeta as _ABCMeta
from abc import abstractmethod as _abstractmethod
from vexbot.extensions import extendmany as _extendmany
from vexbot.extensions import extend as _extend


class Observer(metaclass=_ABCMeta):
    extensions = ()
    def __init__(self, *args, **kwargs):
        extensions = list(self.extensions)
        dicts = [x for x in extensions if isinstance(x, dict)]
        for d in dicts:
            extensions.remove(d)
            self.extend(**d, update=False)
        _extendmany(self.__class__, *extensions)

    @_abstractmethod
    def on_next(self, value):
        return NotImplemented

    @_abstractmethod
    def on_error(self, error):
        return NotImplemented

    @_abstractmethod
    def on_completed(self):
        return NotImplemented

    def extend(self,
               method,
               alias: list=None,
               name: str=None,
               hidden: bool=False,
               instancemethod: bool=False,
               roles: list=None,
               update: bool=True):

        _extend(self.__class__, method, alias, name, hidden, instancemethod, roles)
        update_method = getattr(self, 'update_commands')
        if update and update_method:
            update_method()

    def extendmany(self, *methods):
        _extendmany(self.__class__, *methods)
        update = getattr(self, 'update_commands')
        if update:
            update()
