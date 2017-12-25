import typing
import logging


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
    if level is None:
        return self.root_logger.getEffectiveLevel()
    # NOTE: `setLevel` takes both string and integers. Try to cast to an integer first
    try:
        value = int(level)
    # if we can't cast to an int, it's probably a string
    except ValueError:
        pass

    self.root_logger.setLevel(value)


def set_debug(self, *args, **kwargs) -> None:
    self.root_logger.setLevel(logging.DEBUG)
    try:
        self.messaging.pub_handler.setLevel(logging.DEBUG)
    except Exception:
        pass


def set_info(self, *args, **kwargs) -> None:
    """
    Sets the log level to `INFO`
    """
    self.root_logger.setLevel(logging.INFO)
    try:
        self.messaging.pub_handler.setLevel(logging.INFO)
    except Exception:
        pass

def set_default(self, *args, **kwargs):
    self.root_logger.setLevel(logging.WARN)


def filter_logs(self, *args, **kwargs):
    if not args:
        raise ValueError('Must supply something to filter against!')
    for name in args:
        for handler in self.root_logger.handlers:
            handler.addFilter(logging.Filter(name))


def anti_filter(self, *args, **kwargs):
    def filter_(record: logging.LogRecord):
        if record.name in args:
            return False
        return True
    for handler in self.root_logger.handlers:
        handler.addFilter(filter_)
