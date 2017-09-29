from vexbot.adapters.shell import Shell
from vexbot.adapters.messaging import Messaging as _Messaging


def main(**kwargs):
    shell = Shell(**kwargs)
    return shell.run()


if __name__ == '__main__':
    main()
