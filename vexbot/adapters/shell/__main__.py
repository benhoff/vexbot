from vexbot.adapters.shell import PromptShell
from vexbot.adapters.messaging import ZmqMessaging as _Messaging
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
    # command publish
    # command subscribe
    # heartbeat port
    # control port
    # chatter port

    messaging = _Messaging('shell', )

    command = ShellCommand(**shell_kwargs)
    # TODO: messaging should maybe be separate?
    messaging = command.messaging

    shell = PromptShell(command, **shell_kwargs)
    messaging.set_pong_callback(shell.set_bot_prompt_yes)

    return shell.cmdloop_and_start_messaging()



if __name__ == '__main__':
    main()
