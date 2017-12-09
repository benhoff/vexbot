import logging

from vexbot.intents import intent
from vexbot.observers import CommandObserver
from vexbot.extension import extension
from vexbot.adapters.shell.observers import CommandObserver as ShellObserver


@extension(CommandObserver, alias=['reboot',])
@extension(ShellObserver, alias=['reboot',])
# @intent(name='restart_program')
def restart(self, *args, mode: str='replace', **kwargs) -> None:
    self.logger.info(' restart service %s in mode %s', args, mode)
    for target in args:
        self.subprocess_manager.restart(target, mode)


@extension(CommandObserver, alias=['reboot',])
@extension(ShellObserver, alias=['reboot',])
# @intent(CommandObserver, name='stop_program')
def stop(self, *args, mode: str='replace', **kwargs) -> None:
    self.logger.info(' stop service %s in mode %s', args, mode)
    for target in args:
        self.subprocess_manager.stop(target, mode)


@extension(CommandObserver)
@extension(ShellObserver)
# @intent(CommandObserver, name='get_status')
def status(self, name: str, *args, **kwargs) -> str:
    self.logger.info(' get status for %s', name)
    return self.subprocess_manager.status(name)


@extension(CommandObserver)
@extension(ShellObserver)
# @intent(name='start_program')
def do_start(self, *args, mode: str='replace', **kwargs) -> None:
    """
    Start a program.

    Args:
        name: The name of the serivce. Will often end with `.service` or
            `.target`. If no argument is provided, will default to
            `.service`
        mode:

    Raises:
        GError: if the service is not found
    """
    self.logger.info(' start service %s in mode %s', name, mode)
    for target in args:
        self.subprocess_manager.start(target, mode)
