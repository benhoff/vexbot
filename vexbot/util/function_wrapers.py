import collections as _collections
from vexmessage import Message as VexMessage


def msg_list_wrapper(func: _collections.Callable, number_args: int=None):
    """
    wraps methods that don't take the `msg` type and instead take a list of
    args
    """
    def inner(msg: VexMessage):
        parsed = msg.contents.get('parsed_args')
        if number_args is None:
            return func(parsed)
        elif number_args == 1:
            return func(parsed[0])
        else:
            return func(parsed[:number_args])
        """
        _, arg = _get_command_and_args(msg)
        commands = arg.split()
        if number_args is not None:
            temp = commands[number_args-1:]
            temp.append(' '.join(commands[number_args:]))
            commands = temp

        return func(commands)
        """

    inner.__doc__ = func.__doc__
    return inner


def msg_unpack_args(func: _collections.Callable, number_args: int=None):
    def inner(msg: VexMessage):
        parsed = msg.contents.get('parsed_args')
        if parsed:
            return func(*parsed)
        """
        _, arg = _get_command_and_args(msg)
        commands = arg.split()
        if number_args is not None:
            temp = commands[number_args-1:]
            temp.append(' '.join(commands[number_args:]))
            commands = temp
        return func(*commands)
        """

    inner.__doc__ = func.__doc__
    return inner


def no_arguments(func: _collections.Callable):
    def inner(msg: VexMessage):
        return func()
    return inner
