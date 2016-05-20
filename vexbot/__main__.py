from vexbot.util import start_vexbot
from vexbot.adapters.shell import main as shell_main


def main():
    settings = start_vexbot()
    shell_settings = settings['shell']
    for key in set(shell_settings.keys()):
        value = shell_settings.pop(key)
        shell_settings[key[2:]] = value

    # Launch the shell interface
    shell_main(**shell_settings)


if __name__ == "__main__":
    main()
