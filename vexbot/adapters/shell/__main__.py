from vexbot.adapters.shell import PromptShell
from vexbot.adapters.messaging import Messaging as _Messaging


def main(**kwargs):
    shell = PromptShell(**kwargs)
    return shell.run()


if __name__ == '__main__':
    main()
