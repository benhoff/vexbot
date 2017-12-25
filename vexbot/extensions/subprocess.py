# from vexbot.intents import intent


# @intent(name='restart_program')
def restart(self, *args, mode: str='replace', **kwargs) -> None:
    self.logger.info(' restart service %s in mode %s', args, mode)
    for target in args:
        self.subprocess_manager.restart(target, mode)


# @intent(CommandObserver, name='stop_program')
def stop(self, *args, mode: str='replace', **kwargs) -> None:
    self.logger.info(' stop service %s in mode %s', args, mode)
    for target in args:
        self.subprocess_manager.stop(target, mode)


# @intent(CommandObserver, name='get_status')
def status(self, name: str, *args, **kwargs) -> str:
    self.logger.debug(' get status for %s', name)
    return self.subprocess_manager.status(name)


# @intent(name='start_program')
def start(self, *args, mode: str='replace', **kwargs) -> None:
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
    for target in args:
        self.logger.info(' start service %s in mode %s', target, mode)
        self.subprocess_manager.start(target, mode)


def uptime(self, *args, name: str='vexbot.service', **kwargs):
    return self.subprocess_manager.uptime(name)


uptime._meta = 'process_uptime'
restart._meta = 'restart_process'
start._meta = 'start_process'
status._meta = 'status_process'
stop._meta = 'stop_process'
