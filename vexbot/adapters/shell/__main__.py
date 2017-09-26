from vexbot.adapters.shell import PromptShell
from vexbot.adapters.messaging import Messaging as _Messaging
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

    messaging_defaults = {'service_name': 'shell'}

    command = ShellCommand(**shell_kwargs)
    shell = PromptShell(command, **shell_kwargs)
    command.messaging.set_pong_callback(shell.set_bot_prompt_yes)

    return shell.cmdloop_and_start_messaging()


if __name__ == '__main__':
    main()
