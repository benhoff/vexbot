from vexbot.adapters.shell import Shell


def main(**kwargs):
    shell = Shell(**kwargs)
    return shell.run()


if __name__ == '__main__':
    main()
