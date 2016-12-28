from vexbot.adapters.shell.shell import PromptShell
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
    command = ShellCommand(**shell_kwargs)
    messaging = command.messaging

    # shell is the de-facto view
    shell = PromptShell(command, **shell_kwargs)

    def no_bot(*args, **kwargs):
        shell.set_bot_prompt_no()

    def bot(*args, **kwargs):
        shell.set_bot_prompt_yes()

    controller = ShellController(shell, messaging, **controller_kwargs)
    return controller.cmdloop()


if __name__ == '__main__':
    main()
