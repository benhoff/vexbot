from vexbot.intents import intent
from vexbot.command import extension
from vexbot.observers import CommandObserver


@extension(CommandObserver)
# @intent(name='start_program')
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


@extension(CommandObserver, alias=['reboot',])
# @command(alias=['reboot',])
# @intent(name='restart_program')
def do_restart(self, name: str, mode: str='replace', *args, **kwargs) -> None:
    self.logger.info(' restart service %s in mode %s', name, mode)
    self.subprocess_manager.restart(name, mode)


@extension(CommandObserver)
# @intent(name='stop_program')
def do_stop(self, name: str, mode: str='replace', *args, **kwargs) -> None:
    self.logger.info(' stop service %s in mode %s', name, mode)
    self.subprocess_manager.stop(name, mode)


@extension(CommandObserver)
# @intent(name='get_status')
def do_status(self, name: str) -> str:
    self.logger.info(' get status for %s', name)
    return self.subprocess_manager.status(name)
