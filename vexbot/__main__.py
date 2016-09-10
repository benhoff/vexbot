#!/usr/bin/env python3
import atexit

from vexbot.commands.start_vexbot import start_vexbot
from vexbot.adapters.shell import main as shell_main


def _kill_vexbot(process):
    def inner():
        process.terminate()

    return inner


def main(settings=None):
    if settings is None:
        settings = {}

    process = start_vexbot()
    if process and settings.get('kill_on_exit', False):
        atexit.register(_kill_vexbot(process))

    shell_settings = settings.get('shell', {})
    # TODO: are these next 5 lines needed?
    process = process.poll()
    if process is not None:
        already_running = True
    else:
        already_running = False

    shell_settings['already_running'] = already_running
    # Launch the shell interface
    shell_main(**shell_settings)


if __name__ == "__main__":
    main()
