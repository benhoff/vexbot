import typing
import logging

from vexbot.intents import intent
from vexbot.extension import extension
from vexbot.observers import CommandObserver


@extension(CommandObserver)
@intent(name='get_log')
@intent(name='set_log')
def log_level(self,
              level: typing.Union[str, int]=None,
              *args,
              **kwargs) -> typing.Union[None, str]:
    """
    Args:
        level:

    Returns:
        The log level if a `level` is passed in
    """
    self.root_logger = logging.getLogger()
    if level is None:
        return self.root_logger.getEffectiveLevel()
    # NOTE: `setLevel` takes both string and integers. Try to cast to an integer first
    try:
        value = int(level)
    # if we can't cast to an int, it's probably a string
    except ValueError:
        pass

    self.root_logger.setLevel(value)


@extension(CommandObserver)
def set_log_debug(self, *args, **kwargs) -> None:
    self.root_logger = logging.getLogger()
    self.root_logger.setLevel(logging.DEBUG)
    # FIXME
    self.messaging.pub_handler.setLevel(logging.DEBUG)


@extension(CommandObserver)
def set_log_info(self, *args, **kwargs) -> None:
    """
    Sets the log level to `INFO`
    """
    self.root_logger = logging.getLogger()
    self.root_logger.setLevel(logging.INFO)
    self.messaging.pub_handler.setLevel(logging.INFO)


# FIXME
@extension(CommandObserver)
def filter_logs(self, *args, **kwargs):
    if not args:
        raise ValueError('Must supply something to filter against!')
    for name in args:
        for handler in self._root.handlers:
            handler.addFilter(logging.Filter(name))


# FIXME
@extension(CommandObserver)
def anti_filter(self, *args, **kwargs):
    def filter_(record: logging.LogRecord):
        if record.name in args:
            return False
        return True
    for handler in self._root.handlers:
        handler.addFilter(filter_)
