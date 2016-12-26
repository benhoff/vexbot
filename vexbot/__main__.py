#!/usr/bin/env python3
import atexit

from vexbot.commands.start_vexbot import start_vexbot
from vexbot.adapters.shell.__main__ import main as shell_main


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
    # Launch the shell interface
    shell_main(**shell_settings)
    process.poll()


if __name__ == "__main__":
    debug = {'kill_on_exit': True}
    main(debug)
