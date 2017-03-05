from vexbot.adapters.shell import PromptShell
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

    command = ShellCommand(**shell_kwargs)
    messaging = command.messaging

    shell = PromptShell(command, **shell_kwargs)
    messaging.set_pong_callback(shell.set_bot_prompt_yes)

    return shell.cmdloop_and_start_messaging()



if __name__ == '__main__':
    main()
