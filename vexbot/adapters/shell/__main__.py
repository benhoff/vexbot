from vexbot.adapters.shell.shell import Shell
from vexbot.adapters.shell.controller import ShellController
from vexbot.adapters.shell.command_manager import ShellCommand


def main(controller_kwargs=None,
         shell_kwargs=None,
         command_kwargs=None):

    if controller_kwargs is None:
        controller_kwargs = {}
    if shell_kwargs is None:
        shell_kwargs = {}
    if command_kwargs is None:
        command_kwargs = {}

    # command manager is going to manage the messaging... for now
    command = ShellCommand()
    messaging = command.messaging
    # shell is the de-facto view
    shell = Shell(command, **shell_kwargs)
    controller = ShellController(shell, messaging, **controller_kwargs)
    return controller.cmdloop()


if __name__ == '__main__':
    main()
