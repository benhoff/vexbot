import logging

from vexbot.intents import intent
from vexbot.observers import CommandObserver
from vexbot.command import extension


@extension(CommandObserver, alias=['reboot',])
@intent(name='restart_program')
def restart(self, name: str, mode: str='replace', *args, **kwargs) -> None:
    self.logger.info(' restart service %s in mode %s', name, mode)
    self.subprocess_manager.restart(name, mode)


@extension(CommandObserver)
@intent(CommandObserver, name='stop_program')
def stop(self, name: str, mode: str='replace', *args, **kwargs) -> None:
    self.logger.info(' stop service %s in mode %s', name, mode)
    self.subprocess_manager.stop(name, mode)


@extension(CommandObserver)
@intent(CommandObserver, name='get_status')
def status(self, name: str) -> str:
    self.logger.info(' get status for %s', name)
    return self.subprocess_manager.status(name)


@extension(CommandObserver)
@intent(name='start_program')
def do_start(self, name: str, mode: str='replace', *args, **kwargs) -> None:
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
    self.subprocess_manager.start(name, mode)
